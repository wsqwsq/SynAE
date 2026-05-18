import logging
import re

import numpy as np
import pandas as pd
from pathlib import Path

from pe.llm import HuggingfaceLLM, Request
from transformers import AutoTokenizer

from config import (
    OversampleGenParams,
    FewshotGenParams,
    BlankfillGenParams,
    DropMinGenParams,
    InvalidateGenParams,
)

log = logging.getLogger(__name__)


ORIG_TOOL_CALLS_DF = pd.read_json(
    Path(__file__).parent.parent
    / "orig_data/bfcl/multiturn_base/BFCL_v4_multi_turn_base_tool_calls.json",
    lines=True,
)


def load(filepaths: list[str]):
    orig_df_chunks = []
    for df_fp in filepaths:
        df = pd.read_json(df_fp, lines=True)
        orig_df_chunks.append(df)
    orig_df = pd.concat(orig_df_chunks)
    return orig_df


def preprocess(df: pd.DataFrame):
    orig_df_proc = df.copy(deep=True)

    orig_df_proc = orig_df_proc.merge(
        ORIG_TOOL_CALLS_DF[["id", "ground_truth"]], on="id", how="left"
    )
    orig_df_proc.rename(columns={"ground_truth": "tool_calls"}, inplace=True)

    return orig_df_proc


def postprocess(df: pd.DataFrame):
    # Only oversample/dropmin/invalidate will contain the tool_calls column
    # Blankfilling/fewshot require us to generate the tool_calls using BFCL
    if "tool_calls" in df.columns:
        syn_df = df.drop(columns=["tool_calls"], inplace=False)
        syn_df_tool_calls = df[["id", "tool_calls"]]
        return syn_df, syn_df_tool_calls

    # For blankfilling/fewshot, we need dummy tool calls to run BFCL
    # for the first time
    dummy_tc_list = []
    for question in df["question"]:
        dummy_tc_list.append(["func()" for _ in range(len(question))])
    dummy_tool_calls_df = pd.DataFrame({"id": df["id"], "tool_calls": dummy_tc_list})
    return df, dummy_tool_calls_df


def save(df: pd.DataFrame, fn: str):
    fp = f"{fn}.json"
    df.to_json(fp, orient="records", lines=True)
    log.debug(f"Saved data to {fp}!")


def oversample_gen_bfcl_multiturn_base(df: pd.DataFrame, params: OversampleGenParams):
    n_total = len(df)
    n_dups = np.ceil(params.dup_frac * n_total).astype(int)
    n_other = n_total - n_dups

    # Create ids to select duplicated samples from input dataset
    dup_sample_ids = params.dup_sample_idxs
    times_to_tile = np.ceil(n_dups / len(dup_sample_ids)).astype(int)
    final_dup_sample_ids = np.tile(dup_sample_ids, reps=times_to_tile)[:n_dups]
    final_dup_sample_ids = final_dup_sample_ids.tolist()

    # Create ids to select remaining samples from input dataset
    other_sample_ids = [x for x in list(range(n_total)) if x not in dup_sample_ids]
    rng = np.random.default_rng(params.seed)
    with_replacement = params.with_replacement
    if n_other > len(other_sample_ids):
        log.warning(
            f"Need to sample {n_other} other samples from a set of {len(other_sample_ids)} samples. "
            f"Overriding config, using sampling with replacement."
        )
        with_replacement = True
    final_other_sample_ids = rng.choice(
        a=other_sample_ids, size=n_other, replace=with_replacement
    )
    final_other_sample_ids = final_other_sample_ids.tolist()

    # Construct synthetic dataset using the duplicate ids and other ids
    syn_sample_ids = final_dup_sample_ids
    syn_sample_ids.extend(final_other_sample_ids)
    syn_df = df.iloc[syn_sample_ids]

    # Overwrite id column with new ids
    # This is so we can run bfcl inference easily
    dup_frac_str = str(params.dup_frac).replace(".", "_")
    syn_df["id"] = [f"oversample_frac{dup_frac_str}_{i}" for i in range(len(syn_df))]

    return syn_df


def extract_question_text_for_prompt(question: dict):
    question_str_list = []
    for q_arr in question:
        q_part = q_arr[0]
        if "content" in q_part:
            question_str_list.append(q_part["content"])
    return "\n".join(question_str_list)


def blank_sample(
    sample: str, tokenizer, mask_token: int, blank_probability: float
) -> str:
    """This adds blanks to the sample while being aware of newline characters.
    Newline characters should not be masked for BFCL."""
    lines = sample.split("\n")

    masked_lines = []
    for line in lines:
        input_ids = np.asarray(tokenizer.encode(line, add_special_tokens=False))
        masked_indices = np.random.uniform(size=len(input_ids)) < blank_probability
        input_ids[masked_indices] = mask_token
        masked_lines.append(tokenizer.decode(input_ids, skip_special_tokens=True))

    return "\n".join(masked_lines)


def parse_blankfill_response_for_question(response: str, n_turns: int):
    question = []
    for line in response.strip().split("\n"):
        if not line:
            continue

        # Filter out truncated requests (< 8 words)
        content = line.strip()
        if content and len(content.split()) >= 8:
            question.append([{"role": "user", "content": content}])

    if len(question) != n_turns:
        log.debug(f"Expected {n_turns} turns, got {len(question)}")
        if len(question) > n_turns:
            question = question[:n_turns]

    return question


def blankfill_gen_bfcl_multiturn_base(df: pd.DataFrame, params: BlankfillGenParams):
    """Perform blankfilling generation with BFCL-specific constraints.
    For each original sample, construct the LLM request to generate the synthetic sample as follows:
    1. Format the question field as a string with the user messages
    2. Add blanks according to blank_probability
    3. Ask the LLM to fill in the blanks based on masked string and the initial config.

    Each synthetic sample is then post-processed to match the BFCL format.
    This means we construct a JSON object with id, question, initial_config, path,
    involved_classes, excluded_function.
    Note: The synthetic tool calls need to be generated using BFCL inference.
    """
    hf_llm = HuggingfaceLLM(**params.hf_llm_gen_args)
    tokenizer = AutoTokenizer.from_pretrained(
        params.hf_llm_gen_args["model_name_or_path"]
    )
    mask_token = tokenizer.encode("_", add_special_tokens=False)[0]

    messages_list = []
    system_message = {
        "role": "system",
        "content": (
            "You are a request completion assistant. "
            "Fill in blanks using ONLY the provided APIs and Resources. "
            "Output only the completed requests, one per line. "
            "Do not add explanations or extra text."
        ),
    }

    # Define example to use in all prompts
    example_context = """APIs: GorillaFileSystem
      Resources:                                                                                                                                                 
      - Files: /workspace/documents/report.pdf, /archive/backup/data.txt"""
    example_masked = """Fi__ all P__ files in the '/workspace/do___ents' fol___?
      Af___ that, cop_ them to '/_____/backup' dire____."""
    example_completed = """Find all PDF files in the '/workspace/documents' folder?
      After that, copy them to '/archive/backup' directory."""

    # Mask conversations and construct LLM requests
    conv_list = df["question"].apply(extract_question_text_for_prompt).tolist()
    n_turns_list = df["question"].apply(lambda x: len(x))
    for i, conv in enumerate(conv_list):
        masked_conv_str = blank_sample(
            sample=conv,
            tokenizer=tokenizer,
            mask_token=mask_token,
            blank_probability=params.blank_probability,
        )

        initial_config = df["initial_config"].iloc[i]
        target_resources = extract_config_resources_for_prompt(initial_config)
        target_classes = ", ".join(sorted(initial_config.keys()))

        user_message = {
            "role": "user",
            "content": (
                f"Fill in the blanks (underscores) to complete the user requests.\n"
                f"Example:\n"
                f"{example_context}\n\n"
                f"Input with blanks:\n{example_masked}\n\n"
                f"Completed requests:\n{example_completed}\n\n"
                f"Now fill in the blanks for this:\n"
                f"APIs: {target_classes}\n"
                f"Resources: {target_resources}\n\n"
                f"Input with blanks:\n{masked_conv_str}\n\n"
                f"Completed requests:"
            ),
        }
        messages = [system_message, user_message]
        messages_list.append(messages)

    requests = [Request(messages=messages) for messages in messages_list]
    responses = hf_llm.get_responses(requests)

    # Parse each response and construct BFCL sample
    question_list = []
    involved_classes_list = []
    for i, response in enumerate(responses):
        n_turns = n_turns_list[i]
        res_question = parse_blankfill_response_for_question(response, n_turns)
        res_involved_classes = list(df["initial_config"].iloc[i].keys())

        question_list.append(res_question)
        involved_classes_list.append(res_involved_classes)

    blank_prob_str = str(params.blank_probability).replace(".", "_")
    syn_ids_list = [f"blankfill_prob{blank_prob_str}_{i}" for i in range(len(df))]
    syn_df = pd.DataFrame(
        {
            "id": syn_ids_list,
            "question": question_list,
            "initial_config": df["initial_config"],
            "path": [
                [] for _ in responses
            ],  # Just metadata and not used by BFCL generate/evaluate
            "involved_classes": involved_classes_list,
            "excluded_function": [
                [] for _ in responses
            ],  # Just metadata and not used by BFCL generate/evaluate
        }
    )

    return syn_df


def format_bfcl_sample_for_prompt(sample: dict):
    resources = extract_config_resources_for_prompt(sample["initial_config"])
    requests = "\n".join(
        [
            f"Request {i + 1}: {turn[0]['content']}"
            for i, turn in enumerate(sample["question"])
        ]
    )
    apis = ", ".join(sample["involved_classes"])

    return f"""APIs: {apis}
Resources: {resources}
Requests:
{requests}"""


def extract_config_resources_for_prompt(initial_config: dict):
    parts = []

    if "GorillaFileSystem" in initial_config:
        files = []

        def find_files(node, path=""):
            if isinstance(node, dict):
                if node.get("type") == "file":
                    files.append(path)
                elif "contents" in node:
                    for name, child in node["contents"].items():
                        find_files(child, f"{path}/{name}" if path else name)
                else:
                    for v in node.values():
                        if isinstance(v, dict):
                            find_files(v)

        find_files(initial_config["GorillaFileSystem"])
        if files:
            parts.append(f"Files: {', '.join(files)}")

    if "TwitterAPI" in initial_config:
        t = initial_config["TwitterAPI"]
        parts.append(
            f"Twitter: @{t.get('username', 'user')} ({len(t.get('tweets', {}))} tweets)"
        )

    if "TradingBot" in initial_config:
        t = initial_config["TradingBot"]
        stocks = list(t.get("stocks", {}).keys())
        parts.append(
            f"Trading: {', '.join(stocks)} (${t.get('account_info', {}).get('balance', 0)})"
        )

    if "VehicleControlAPI" in initial_config:
        v = initial_config["VehicleControlAPI"]
        parts.append(
            f"Vehicle: {v.get('fuelLevel')}L fuel, engine {v.get('engineState')}"
        )

    for api in ["MessageAPI", "TicketAPI", "MathAPI", "TravelAPI"]:
        if api in initial_config:
            parts.append(f"{api} available")

    return "\n".join(f"- {p}" for p in parts)


def parse_fewshot_response_for_question(response: str, n_turns: int):
    question = []
    for line in response.strip().split("\n"):
        if not line:
            continue

        # Remove Request: tags if present
        content = line.strip()
        while content.startswith("Request ") and ":" in content:
            content = content.split(":", 1)[1].strip()

        # Filter out truncated requests (< 8 words)
        if content and len(content.split()) >= 8:
            question.append([{"role": "user", "content": content}])

    if len(question) != n_turns:
        log.debug(f"Expected {n_turns} turns, got {len(question)}")
        if len(question) > n_turns:
            question = question[:n_turns]

    return question


def fewshot_gen_bfcl_multiturn_base(df: pd.DataFrame, params: FewshotGenParams):
    """Perform fewshot generation with BFCL-specific constraints.
    For each synthetic sample, construct the LLM request as follows:
    1. Randomly choose k examples from the original df.
    2. Randomly choose an initial_config (contains proper resource names for the LLM's reference).
    3. Ask the LLM to generate the user messages based on the sampled initial_config.

    Each synthetic sample is then post-processed to match the BFCL format.
    This means we construct a JSON object with id, question, initial_config, path,
    involved_classes, excluded_function.
    Note: The synthetic tool calls need to be generated using BFCL inference.
    """
    n_syn = len(df)

    hf_llm = HuggingfaceLLM(**params.hf_llm_gen_args)

    # Setup for few shot generation
    sample_ids = df["id"].unique()
    rng = np.random.default_rng(params.seed)
    fewshot_sample_ids = rng.choice(sample_ids, size=params.n_examples)

    # Sample a set of initial_configs from the original dataset
    # TODO: We can construct template initial_configs if we don't want to use
    # the original dataset
    ref_config_ids = rng.choice(sample_ids, size=n_syn)
    ref_initial_configs = [
        df[df["id"] == ref_id]["initial_config"].iloc[0] for ref_id in ref_config_ids
    ]

    system_message = {
        "role": "system",
        "content": (
            "You are a test case generator. "
            "Output each request as:\n"
            "Request 1: <request text>\n"
            "Request 2: <request text>"
        ),
    }

    # Construct LLM requests
    messages_list = []
    n_turns_list = []
    for i in range(n_syn):
        # Sample few shot examples if seed is None, otherwise reuse ones sampled above
        if params.seed is None:
            fewshot_sample_ids = rng.choice(sample_ids, size=params.n_examples)

        # Format examples for prompt
        fewshot_df = df[df["id"].isin(fewshot_sample_ids)]
        fewshot_dicts = fewshot_df.to_dict("records")
        examples_str = "\n\n".join(
            [format_bfcl_sample_for_prompt(ex) for ex in fewshot_dicts]
        )

        # Extract information for the LLM from the reference initial_config
        initial_config = ref_initial_configs[i]
        target_resources = extract_config_resources_for_prompt(initial_config)
        target_classes = ", ".join(sorted(initial_config.keys()))

        # Configure sample requirements
        n_turns = rng.choice(
            [2, 3, 4, 5]
        )  # Most common lengths in the original dataset
        n_turns_list.append(n_turns)

        user_message = {
            "role": "user",
            "content": (
                f"{examples_str}\n\n"
                f"Generate EXACTLY {n_turns} requests for the situation below.\n"
                f"Requests can query information, perform operations, modify resources, or search/filter data.\n"
                f"Keep requests realistic. Later requests should build on earlier ones.\n\n"
                f"ONLY refer to the APIs and Resources below in the requests."
                f"APIs: {target_classes}\n"
                f"Resources: {target_resources}\n"
                f"Requests:"
            ),
        }
        messages_list.append([system_message, user_message])

    requests = [Request(messages=messages) for messages in messages_list]
    responses = hf_llm.get_responses(requests)

    # Parse each response and construct BFCL sample
    question_list = []
    involved_classes_list = []
    for i, response in enumerate(responses):
        res_question = parse_fewshot_response_for_question(response, n_turns_list[i])
        res_involved_classes = list(ref_initial_configs[i].keys())

        question_list.append(res_question)
        involved_classes_list.append(res_involved_classes)

    fewshot_str = "fewshot_fixed" if params.seed is not None else "fewshot_rand"
    syn_ids_list = [f"{fewshot_str}_ex{params.n_examples}_{i}" for i in range(n_syn)]
    syn_df = pd.DataFrame(
        {
            "id": syn_ids_list,
            "question": question_list,
            "initial_config": ref_initial_configs,
            "path": [
                [] for _ in responses
            ],  # Just metadata and not used by BFCL generate/evaluate
            "involved_classes": involved_classes_list,
            "excluded_function": [
                [] for _ in responses
            ],  # Just metadata and not used by BFCL generate/evaluate
        }
    )

    return syn_df


def dropmin_gen_bfcl_multiturn_base(df, params: DropMinGenParams):
    """Generates synthetic data by dropping a frac amount of samples from
    each of the k-least frequent class values for the specified minority class.
    """
    class_df = pd.read_csv(params.class_df_fp)
    min_class_value_counts = (
        class_df[params.min_class_name].value_counts().sort_values(ascending=True)
    )
    min_values = min_class_value_counts.keys()[: params.drop_n_min]

    rng = np.random.default_rng(params.seed)

    dropped_ids = []
    for min_value in min_values:
        ids_with_min_value = class_df[class_df[params.min_class_name] == min_value][
            "id"
        ]
        size = int(len(ids_with_min_value) * params.drop_per_class_frac)
        selected_ids = rng.choice(ids_with_min_value, size)
        dropped_ids.extend(selected_ids)

    all_ids = df["id"].unique()
    remaining_ids = set(all_ids) - set(dropped_ids)
    syn_df = df[df["id"].isin(remaining_ids)].copy()

    # Overwrite id column with new ids
    # This is so we can run bfcl inference easily
    drop_frac_str = str(params.drop_per_class_frac).replace(".", "_")
    syn_df["id"] = [
        f"dropmin_{params.drop_n_min}{params.min_class_name}_frac{drop_frac_str}_{i}"
        for i in range(len(syn_df))
    ]
    return syn_df


def invalidate_tool_calls(tc: list[list[str]]) -> list[list[str]]:
    invalid_tc = []
    for turn_tc in tc:
        invalid_turn_tc = []
        for step_tc in turn_tc:
            corrupted = re.sub(r"'[^']*'", "'invalid'", step_tc)
            invalid_turn_tc.append(corrupted)
        invalid_tc.append(invalid_turn_tc)
    return invalid_tc


def invalidate_gen_bfcl_multiturn_base(df, params: InvalidateGenParams):
    """Generates synthetic data by invalidating the tool calls field for the
    specified frac of samples.
    """
    all_ids = df["id"].unique()

    # Randomly select IDs to invalidate
    rng = np.random.default_rng(params.seed)
    size = int(len(all_ids) * params.invalidate_frac)
    invalid_ids = rng.choice(all_ids, size)

    # Invalidate tool calls for the selected IDs
    syn_df = df.copy()
    mask = syn_df["id"].isin(invalid_ids)
    syn_df.loc[mask, "tool_calls"] = syn_df.loc[mask, "tool_calls"].apply(
        invalidate_tool_calls
    )

    # Overwrite id column with new ids
    # This is so we can run bfcl inference easily
    inv_frac_str = str(params.invalidate_frac).replace(".", "_")
    syn_df["id"] = [f"invalidate_frac{inv_frac_str}_{i}" for i in range(len(syn_df))]
    return syn_df


PIPELINE = {
    "load": load,
    "preprocess": preprocess,
    "postprocess": postprocess,
    "save": save,
    "oversample_gen": oversample_gen_bfcl_multiturn_base,
    "blankfill_gen": blankfill_gen_bfcl_multiturn_base,
    "fewshot_gen": fewshot_gen_bfcl_multiturn_base,
    "dropmin_gen": dropmin_gen_bfcl_multiturn_base,
    "invalidate_gen": invalidate_gen_bfcl_multiturn_base,
}
