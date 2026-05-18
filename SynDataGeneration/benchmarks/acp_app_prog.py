import logging

import numpy as np
import pandas as pd
from transformers import AutoTokenizer

from pe.llm import HuggingfaceLLM, Request

from config import (
    OversampleGenParams,
    FewshotGenParams,
    BlankfillGenParams,
    DropMinGenParams,
    InvalidateGenParams,
)

log = logging.getLogger(__name__)


def load(filepaths: list[str]):
    orig_df_chunks = []
    for df_fp in filepaths:
        df = pd.read_csv(df_fp)
        orig_df_chunks.append(df)
    orig_df = pd.concat(orig_df_chunks)
    return orig_df


def preprocess(df: pd.DataFrame):
    return df


def postprocess(df: pd.DataFrame):
    return df, None


def save(df: pd.DataFrame, fn: str):
    fp = f"{fn}.csv"
    df.to_csv(fp, index=False)
    log.debug(f"Saved data to {fp}!")


def oversample_gen_acp_app_prog(df: pd.DataFrame, params: OversampleGenParams):
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
    dup_frac_str = str(params.dup_frac).replace(".", "_")
    syn_df["id"] = [f"oversample_frac{dup_frac_str}_{i}" for i in range(len(syn_df))]

    return syn_df


BLANKFILL_EXAMPLE_STR = """\
Example 1:
Context: This is a ferry domain, where the task is to transport cars from their start to their goal locations, using a ferry. Each location is accessible by ferry from each other location. The cars can be debarked or boarded, and the ferry can carry only one car at a time. There are 3 locations and 10 cars, numbered consecutively. Currently, the ferry is at l1, with the car c2 on board. The cars are at locations as follows: c6, c3, and c0 are at l2; c4, c9, and c7 are at l0; c1, c8, and c5 are at l1.
Group: applicable_actions_bool
Answer: yes
Masked question: Is the fol___ing action appl___able in this state: deb_rk the car c2 fr_m the ferry to loc_tion l1?
Completed question: Is the following action applicable in this state: debark the car c2 from the ferry to location l1?

Example 2:
Context: This is a ferry domain, where the task is to transport cars from their start to their goal locations, using a ferry. Each location is accessible by ferry from each other location. The cars can be debarked or boarded, and the ferry can carry only one car at a time. There are 3 locations and 10 cars, numbered consecutively. Currently, the ferry is at l1 location and it is empty. The cars are at locations as follows: c9, c4, and c6 are at l0; c0, c8, c1, c7, and c2 are at l1; c3 and c5 are at l2.
Group: progression_bool
Answer: no
Masked question: Will the f_ct "The ferry is emp__" hold aft__ perf___ing the act_on "emb_rk the car c0 at loc_tion l1 on to the ferry" in the cur_ent state?
Completed question: Will the fact "The ferry is empty" hold after performing the action "embark the car c0 at location l1 on to the ferry" in the current state?\
"""


def blank_sample(
    sample: str, tokenizer, mask_token: int, blank_probability: float
) -> str:
    input_ids = np.asarray(tokenizer.encode(sample, add_special_tokens=False))
    masked_indices = np.random.uniform(size=len(input_ids)) < blank_probability
    input_ids[masked_indices] = mask_token
    return tokenizer.decode(input_ids, skip_special_tokens=True)


def parse_blankfill_response_for_question(response: str) -> str:
    for line in response.strip().split("\n"):
        content = line.strip()
        if not content:
            continue

        if content.lower().startswith("completed question:"):
            content = content.split(":", 1)[1].strip()

        # Filter out truncated requests (< 8 words)
        if len(content.split()) >= 8:
            return content
    return ""


def blankfill_gen_acp_app_prog(df: pd.DataFrame, params: BlankfillGenParams):
    """Perform blankfilling generation with ACP-specific constraints.
    For each original sample, construct the LLM request as follows:
    1. Mask tokens in the question field according to blank_probability.
    2. Ask the LLM to fill in the blanks using the full context as reference.

    Each synthetic sample retains the original context, group, and answer.
    """
    hf_llm = HuggingfaceLLM(**params.hf_llm_gen_args)
    tokenizer = AutoTokenizer.from_pretrained(
        params.hf_llm_gen_args["model_name_or_path"]
    )
    mask_token = tokenizer.encode("_", add_special_tokens=False)[0]

    system_message = {
        "role": "system",
        "content": (
            "You are a question completion assistant. "
            "Fill in the blanks (underscores) to complete the question. "
            "Use ONLY entities and terms from the provided context. "
            "Output ONLY the completed question text."
        ),
    }

    messages_list = []
    for _, row in df.iterrows():
        masked_question = blank_sample(
            sample=row["question"],
            tokenizer=tokenizer,
            mask_token=mask_token,
            blank_probability=params.blank_probability,
        )
        user_message = {
            "role": "user",
            "content": (
                f"Fill in the blanks to complete the question. "
                f"Use ONLY entities from the context.\n\n"
                f"{BLANKFILL_EXAMPLE_STR}\n\n"
                f"Now complete this:\n"
                f"Context: {row['context']}\n"
                f"Group: {row['group']}\n"
                f"Answer: {row['answer']}\n"
                f"Masked question: {masked_question}\n"
                f"Completed question:"
            ),
        }
        messages_list.append([system_message, user_message])

    requests = [Request(messages=messages) for messages in messages_list]
    responses = hf_llm.get_responses(requests)

    question_list = [parse_blankfill_response_for_question(r) for r in responses]

    blank_prob_str = str(params.blank_probability).replace(".", "_")
    syn_ids_list = [f"blankfill_prob{blank_prob_str}_{i}" for i in range(len(df))]
    syn_df = pd.DataFrame(
        {
            "id": syn_ids_list,
            "group": df["group"],
            "context": df["context"],
            "question": question_list,
            "answer": df["answer"],
        }
    )

    return syn_df


def format_acp_sample_for_prompt(sample: dict) -> str:
    # Truncate context to first sentence to keep prompts within context window limits
    first_sentence = sample["context"].split(".")[0] + "."
    return f"Context: {first_sentence}\nQuestion: {sample['question']}\nAnswer: {sample['answer']}"


def parse_fewshot_response_for_question(response: str) -> str:
    for line in response.strip().split("\n"):
        content = line.strip()
        if not content:
            continue
        if content.lower().startswith("question:"):
            content = content.split(":", 1)[1].strip()
        return content
    return ""


def fewshot_gen_acp_app_prog(df: pd.DataFrame, params: FewshotGenParams):
    """Perform fewshot generation with ACP-specific constraints.
    For each synthetic sample, construct the LLM request as follows:
    1. Randomly choose k // 2 fewshot examples from each group (app and prog).
    2. Randomly choose a reference sample whose context and group will be passed to the LLM for generation.
    3. Uniformly sample a reference answer (yes/no).
    4. Ask the LLM to generate a matching question for the reference context, group, and answer.
    """
    n_syn = len(df)

    hf_llm = HuggingfaceLLM(**params.hf_llm_gen_args)

    groups = ["applicable_actions_bool", "progression_bool"]
    group_ids = {g: df[df["group"] == g]["id"].unique() for g in groups}

    # Setup for few shot generation
    sample_ids = df["id"].unique()
    rng = np.random.default_rng(params.seed)

    n_per_group = params.n_examples // 2
    fewshot_ids_per_group = {
        g: rng.choice(group_ids[g], size=n_per_group) for g in groups
    }

    ref_ids = rng.choice(sample_ids, size=n_syn)
    ref_samples = [df[df["id"] == rid].iloc[0].to_dict() for rid in ref_ids]
    fixed_answers = rng.choice(["yes", "no"], size=n_syn)

    system_message = {
        "role": "system",
        "content": (
            "You are a test case generator for planning domain tasks. "
            "Given a context and examples, generate a single question that has the specified answer. "
            "Output ONLY the question text with no preamble or label."
        ),
    }

    messages_list = []
    for i in range(n_syn):
        if params.seed is None:
            fewshot_ids_per_group = {
                g: rng.choice(group_ids[g], size=n_per_group) for g in groups
            }

        fewshot_dicts = []
        for g in groups:
            fewshot_dicts.extend(
                df[df["id"].isin(fewshot_ids_per_group[g])].to_dict("records")
            )
        examples_str = "\n\n".join(
            [format_acp_sample_for_prompt(ex) for ex in fewshot_dicts]
        )

        ref = ref_samples[i]
        user_message = {
            "role": "user",
            "content": (
                f"Examples:\n{examples_str}\n\n"
                f"Generate a question of type '{ref['group']}' for the context below "
                f"such that the answer is '{fixed_answers[i]}'.\n\n"
                f"Context: {ref['context']}\n\n"
                f"Question:"
            ),
        }
        messages_list.append([system_message, user_message])

    requests = [Request(messages=messages) for messages in messages_list]
    responses = hf_llm.get_responses(requests)

    question_list = [parse_fewshot_response_for_question(r) for r in responses]

    fewshot_str = "fewshot_fixed" if params.seed is not None else "fewshot_rand"
    syn_ids_list = [f"{fewshot_str}_ex{params.n_examples}_{i}" for i in range(n_syn)]
    syn_df = pd.DataFrame(
        {
            "id": syn_ids_list,
            "group": [ref["group"] for ref in ref_samples],
            "context": [ref["context"] for ref in ref_samples],
            "question": question_list,
            "answer": fixed_answers.tolist(),
        }
    )

    return syn_df


def dropmin_gen_acp_app_prog(df: pd.DataFrame, params: DropMinGenParams):
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
    drop_frac_str = str(params.drop_per_class_frac).replace(".", "_")
    syn_df["id"] = [
        f"dropmin_{params.drop_n_min}{params.min_class_name}_frac{drop_frac_str}_{i}"
        for i in range(len(syn_df))
    ]
    return syn_df


def invalidate_gen_acp_app_prog(df: pd.DataFrame, params: InvalidateGenParams):
    """Generates synthetic data by invalidating the output field for the
    specified frac of samples.
    """
    all_ids = df["id"].unique()

    # Randomly select IDs to invalidate
    rng = np.random.default_rng(params.seed)
    size = int(len(all_ids) * params.invalidate_frac)
    invalid_ids = rng.choice(all_ids, size)

    # Invalidate outputs for the selected IDs
    syn_df = df.copy()
    mask = syn_df["id"].isin(invalid_ids)
    flip_answer_map = {"yes": "no", "no": "yes"}
    syn_df.loc[mask, "answer"] = syn_df.loc[mask, "answer"].map(flip_answer_map)

    # Overwrite id column with new ids
    inv_frac_str = str(params.invalidate_frac).replace(".", "_")
    syn_df["id"] = [f"invalidate_frac{inv_frac_str}_{i}" for i in range(len(syn_df))]
    return syn_df


PIPELINE = {
    "load": load,
    "preprocess": preprocess,
    "postprocess": postprocess,
    "save": save,
    "oversample_gen": oversample_gen_acp_app_prog,
    "blankfill_gen": blankfill_gen_acp_app_prog,
    "fewshot_gen": fewshot_gen_acp_app_prog,
    "dropmin_gen": dropmin_gen_acp_app_prog,
    "invalidate_gen": invalidate_gen_acp_app_prog,
}
