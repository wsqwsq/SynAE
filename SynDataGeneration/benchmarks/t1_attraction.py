import logging
import numpy as np
import pandas as pd
from pe.llm import HuggingfaceLLM, Request
from transformers import AutoTokenizer

from config import (
    BlankfillGenParams,
    FewshotGenParams,
    OversampleGenParams,
    DropMinGenParams,
)

log = logging.getLogger(__name__)


def load(filepaths: list[str]):
    orig_df_chunks = []
    i_chunk = 0
    for df_fp in filepaths:
        df = pd.read_csv(df_fp)
        for g_name, g_df in df.groupby("ID"):
            corrected_id_df = pd.DataFrame(
                {
                    "ID": [i_chunk] * len(g_df),
                    "Template": g_df["Template"],
                    "Plan": g_df["Plan"],
                    "Filled_Template": g_df["Filled_Template"],
                    "Filled_Plan": g_df["Filled_Plan"],
                }
            )
            orig_df_chunks.append(corrected_id_df)
            i_chunk += 1
    orig_df = pd.concat(orig_df_chunks)
    return orig_df


def preprocess(df: pd.DataFrame):
    orig_df_proc = (
        df[["ID", "Filled_Template"]]
        .groupby("ID")
        .agg(lambda x: "\n".join(x))
        .reset_index()
    )
    return orig_df_proc


def get_valid_lines(conv: str) -> list[str]:
    lines = conv.split("\n")

    # Remove empty lines
    # Remove lines that don't start with user: or assistant:
    valid_lines = []
    for ln in lines:
        if ln.strip() not in (None, "", "\n"):
            if ln.lower().startswith("user:") or ln.lower().startswith("assistant:"):
                valid_lines.append(ln)

    return valid_lines


def postprocess(df: pd.DataFrame):
    syn_ids_list = []
    syn_conv_lines_list = []
    for i, syn_conv in enumerate(df["Filled_Template"]):
        fixed_syn_conv_lines = get_valid_lines(str(syn_conv))
        syn_ids_list.extend([i] * len(fixed_syn_conv_lines))
        syn_conv_lines_list.extend(fixed_syn_conv_lines)

    syn_df = pd.DataFrame({"ID": syn_ids_list, "Filled_Template": syn_conv_lines_list})
    return syn_df, None


def save(df: pd.DataFrame, fn: str):
    fp = f"{fn}.csv"
    df.to_csv(fp, index=False)
    log.debug(f"Saved data to {fp}!")


def oversample_gen_t1_attraction(df: pd.DataFrame, params: OversampleGenParams):
    """Generates synthetic data by duplicating specified samples
    until they reach params.dup_frac percentage of the full dataset.
    Other samples are randomly chosen with replacement from the
    remaining dataset.
    """
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
    return syn_df


def blank_sample(
    sample: str, tokenizer, mask_token: int, blank_probability: float
) -> str:
    input_ids = np.asarray(tokenizer.encode(sample, add_special_tokens=False))
    masked_indices = np.random.uniform(size=len(input_ids)) < blank_probability
    input_ids[masked_indices] = mask_token
    return tokenizer.decode(input_ids, skip_special_tokens=True)


def blankfill_gen_t1_attraction(df, params: BlankfillGenParams):
    hf_llm = HuggingfaceLLM(**params.hf_llm_gen_args)
    tokenizer = AutoTokenizer.from_pretrained(
        params.hf_llm_gen_args["model_name_or_path"]
    )
    mask_token = tokenizer.encode("_", add_special_tokens=False)[0]

    messages_list = []
    system_message = {
        "role": "system",
        "content": "You are a helpful conversation generator. "
        "When given a conversation with blanks (underscores), fill them in naturally. "
        "IMPORTANT RULES:\n"
        "1. The conversation MUST start with 'assistant:' (not 'Assistant:' or any variation)\n"
        "2. Lines MUST alternate strictly between 'user:' and 'assistant:'\n"
        "3. Each line must follow the format: 'role: content' where role is either 'user' or 'assistant'\n"
        "4. Output ONLY the completed conversation with no preamble, explanation, or extra text\n"
        "5. Maintain the same number of conversation turns as the input",
    }

    # Mask conversations and construct LLM requests
    conv_list = df["Filled_Template"]
    for i, conv in enumerate(conv_list):
        masked_conv = ""
        for line in conv.split("\n"):
            prefix_part, separator, content = line.partition(": ")
            masked_content = blank_sample(
                tokenizer=tokenizer,
                mask_token=mask_token,
                sample=content,
                blank_probability=params.blank_probability,
            )
            masked_line = prefix_part + separator + masked_content
            masked_conv += masked_line + "\n"

        user_message = {
            "role": "user",
            "content": f"Example input for fill in the blanks:\n\n"
            f"assistant: H_____ What ____ of attractions are you looking for? Are you interested in _______, a__, or something else?\n"
            f"user: I'm interested in ___ and ____ attractions in __.\n"
            f"assistant: G_ has a lot to offer. Are you looking at specific ______ or re_____?\n"
            f"user: Yeah, I'm thinking of visiting Fre___ and M______.\n"
            f"assistant: Both _____o and ____his have great A__ and S_____ attractions. Let me tell you about some of them.\n"
            f"user: That sounds _____.\n\n"
            f"Completed conversation for example input:\n"
            f"assistant: Hello! What kind of attractions are you looking for? Are you interested in history, art, or something else?\n"
            f"user: I'm interested in Art and Scenic attractions in GA.\n"
            f"assistant: GA has a lot to offer. Are you looking at specific cities or regions?\n"
            f"user: Yeah, I'm thinking of visiting Fresno and Memphis.\n"
            f"assistant: Both Fresno and Memphis have great Art and Scenic attractions. Let me tell you about some of them.\n"
            f"user: That sounds great.\n\n"
            f"Now fill in the blanks to complete this conversation:\n\n{masked_conv}\nCompleted conversation:\n",
        }
        messages = [system_message, user_message]
        messages_list.append(messages)

    requests = [Request(messages=messages) for messages in messages_list]
    responses = hf_llm.get_responses(requests)

    # Fix responses that don't start with "assistant:"
    fixed_responses = []
    for response in responses:
        response = response.strip()
        if not response.startswith("assistant:"):
            response = "assistant: " + response
        fixed_responses.append(response)

    syn_df = pd.DataFrame(
        {"ID": list(range(len(responses))), "Filled_Template": fixed_responses}
    )
    return syn_df


def fewshot_gen_t1_attraction(df, params: FewshotGenParams):
    n_syn = len(df)

    hf_llm = HuggingfaceLLM(**params.hf_llm_gen_args)

    # Setup for few shot generation
    sample_ids = df["ID"].unique()
    rng = np.random.default_rng(params.seed)
    fewshot_sample_ids = rng.choice(sample_ids, size=params.n_examples)

    system_message = {
        "role": "system",
        "content": "You are a helpful conversation generator. "
        "IMPORTANT RULES:\n"
        "1. The conversation MUST start with 'assistant:' (not 'Assistant:' or any variation)\n"
        "2. Lines MUST alternate strictly between 'user:' and 'assistant:'\n"
        "3. Each line must follow the format: 'role: content' where role is either 'user' or 'assistant'\n"
        "4. Output ONLY the completed conversation with no preamble, explanation, or extra text\n"
        "5. The completed conversation must have 6 turns",
    }

    # Construct LLM requests
    messages_list = []
    for i in range(n_syn):
        # Sample few shot examples if seed is None, otherwise reuse ones sampled above
        if params.seed is None:
            fewshot_sample_ids = rng.choice(sample_ids, size=params.n_examples)
        fewshot_df = df[df["ID"].isin(fewshot_sample_ids)]
        conv_list = fewshot_df["Filled_Template"]
        conv_list_str = "\n\n".join(conv_list)

        user_message = {
            "role": "user",
            "content": f"Here are example conversations:\n{conv_list_str}\n\n"
            f"Generate 1 new similar conversation that follows the same structure."
            f"Do not include anything other than this conversation.\n"
            f"Similar conversation:\n",
        }
        messages_list.append([system_message, user_message])

    requests = [Request(messages=messages) for messages in messages_list]
    responses = hf_llm.get_responses(requests)

    # Fix responses that don't start with "assistant:"
    # Keep the first 6 valid conversation turns
    fixed_responses = []
    for response in responses:
        response = response.strip()
        if not response.startswith("assistant:"):
            response = "assistant: " + response
        valid_lines = get_valid_lines(response)[:6]
        response = "\n".join(valid_lines)
        fixed_responses.append(response)

    syn_df = pd.DataFrame(
        {"ID": list(range(len(responses))), "Filled_Template": fixed_responses}
    )
    return syn_df


def dropmin_gen_t1_attraction(df, params: DropMinGenParams):
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
            "ID"
        ]
        size = int(len(ids_with_min_value) * params.drop_per_class_frac)
        selected_ids = rng.choice(ids_with_min_value, size)
        dropped_ids.extend(selected_ids)

    all_ids = df["ID"].unique()
    remaining_ids = set(all_ids) - set(dropped_ids)
    syn_df = df[df["ID"].isin(remaining_ids)]
    return syn_df


PIPELINE = {
    "load": load,
    "preprocess": preprocess,
    "postprocess": postprocess,
    "save": save,
    "oversample_gen": oversample_gen_t1_attraction,
    "blankfill_gen": blankfill_gen_t1_attraction,
    "fewshot_gen": fewshot_gen_t1_attraction,
    "dropmin_gen": dropmin_gen_t1_attraction,
}
