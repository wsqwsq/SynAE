import argparse
import os
import re
from typing import Optional

import numpy as np
import pandas as pd
from vllm import LLM, SamplingParams

GEN_MODEL = "meta-llama/Llama-3.1-8B-Instruct"
GEN_TEMPERATURE = 0.5
GEN_MAX_TOKENS = 200

INPUT_FP = "orig_valid.csv"
OUTPUT_DIR = "syn_case_study"
ONTOLOGY_FP = "ontology_t1_attraction_data.csv"

DROP_FRAC = 0.9
N_FEWSHOT_EXAMPLES = 1
SEED = 123


def get_type(data: str, types: list) -> Optional[str]:
    """Classify sample according to attraction_type, like structbench_syndata does."""
    for t in types:
        if re.search(rf"\b{re.escape(t)}\b", data):
            return t
    return None


def get_valid_lines(conv: str) -> list[str]:
    valid_lines = []

    # Remove empty lines
    # Remove lines that don't start with user: or assistant:
    for ln in conv.split("\n"):
        if ln.strip() not in (None, "", "\n"):
            if ln.lower().startswith("user:") or ln.lower().startswith("assistant:"):
                valid_lines.append(ln)
    return valid_lines


def dropmin_gen(df: pd.DataFrame, types: list, rng) -> tuple:
    type_series = df["Data"].apply(lambda d: get_type(d, types))

    type_counts = type_series.value_counts().sort_values(ascending=True)
    n_min = len(type_counts) // 2
    min_types = type_counts.index[:n_min].tolist()

    dropped_idxs = []
    dropped_info = []
    for t in min_types:
        idxs_with_type = df.index[type_series == t].tolist()
        n_drop = int(DROP_FRAC * len(idxs_with_type))
        selected = rng.choice(idxs_with_type, size=n_drop, replace=False).tolist()
        dropped_idxs.extend(selected)
        dropped_info.append((t, n_drop))

    base_df = df.drop(index=dropped_idxs).reset_index(drop=True)
    return base_df, dropped_info


def attempt1_gen_full(
    base_df: pd.DataFrame, dropped_info: list, types: list, rng
) -> pd.DataFrame:
    aug_rows = []
    for target_type, n_to_add in dropped_info:
        sampled_positions = rng.choice(len(base_df), size=n_to_add, replace=False)
        for pos in sampled_positions:
            row = base_df.iloc[pos]
            orig_type = get_type(row["Data"], types)
            new_data = (
                re.sub(
                    r"\b" + re.escape(orig_type) + r"\b",
                    target_type,
                    row["Data"],
                    flags=re.IGNORECASE,
                )
                if orig_type
                else row["Data"]
            )
            aug_rows.append(
                {
                    "ID": row["ID"],
                    "Data": new_data,
                    "Tool Call": row["Tool Call"],
                    "Output": row["Output"],
                }
            )

    aug_df = pd.DataFrame(aug_rows)
    syn_df = pd.concat([base_df, aug_df], ignore_index=True)
    syn_df["ID"] = list(range(len(syn_df)))
    return syn_df


def build_fewshot_conv(examples: list[str], target_type: str) -> list[dict]:
    system_message = {
        "role": "system",
        "content": (
            "You are a helpful conversation generator. "
            "IMPORTANT RULES:\n"
            "1. The conversation MUST start with 'assistant:'\n"
            "2. Lines MUST alternate strictly between 'user:' and 'assistant:'\n"
            "3. Each line must follow the format: 'role: content'\n"
            "4. Output ONLY the conversation with no preamble or extra text\n"
        ),
    }

    user_message = {
        "role": "user",
        "content": (
            f"Here are example conversations about {target_type} attractions:\n\n"
            f"{chr(10).join(examples)}\n\n"
            f"Generate 1 new similar conversation about {target_type} attractions.\n"
            f"Similar conversation:\n"
        ),
    }

    return [system_message, user_message]


def attempt2_gen_aug(
    orig_df: pd.DataFrame,
    dropped_info: list,
    types: list,
    llm: LLM,
    sampling_params: SamplingParams,
    rng,
) -> pd.DataFrame:
    type_series = orig_df["Data"].apply(lambda d: get_type(d, types))

    convs = []
    conv_meta = []
    for target_type, n_to_add in dropped_info:
        example_idxs = orig_df.index[type_series == target_type].tolist()
        fewshot_idxs = rng.choice(
            example_idxs, size=min(N_FEWSHOT_EXAMPLES, len(example_idxs)), replace=False
        )
        examples = orig_df.loc[fewshot_idxs, "Data"].tolist()

        for _ in range(n_to_add):
            convs.append(build_fewshot_conv(examples, target_type))
            conv_meta.append(target_type)

    print(f"Running fewshot generation for {len(convs)} samples...")
    outputs = llm.chat(convs, sampling_params, use_tqdm=True)

    aug_rows = []
    for i, output in enumerate(outputs):
        response = output.outputs[0].text.strip()
        if not response.lower().startswith("assistant:"):
            response = "assistant: " + response

        # Keep the first 6 valid conversation turns
        valid_lines = get_valid_lines(response)[:6]
        data = "\n".join(valid_lines)
        aug_rows.append(
            {
                "ID": i,
                "Data": data,
            }
        )

    aug_df = pd.DataFrame(aug_rows)
    return aug_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate T1 case study datasets")
    parser.add_argument(
        "--num-gpus", type=int, default=2, help="Number of GPUs for tensor parallelism"
    )
    args = parser.parse_args()

    print(f"Loading data from {INPUT_FP}")
    df = pd.read_csv(INPUT_FP)

    print(f"Loading ontology from {ONTOLOGY_FP}")
    ontology_df = pd.read_csv(ONTOLOGY_FP)
    types = ontology_df["type"].unique().tolist()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Save original df as Dataset 4: Ideal
    ideal_output_fp = f"{OUTPUT_DIR}/ideal.csv"
    df.to_csv(ideal_output_fp, index=False)
    print(f"Saved ideal dataset ({len(df)} samples) to {ideal_output_fp}!")

    rng = np.random.default_rng(SEED)

    # Dataset 1: Base
    # Dropmin
    print("Generating base dataset...")
    base_df, dropped_info = dropmin_gen(df, types, rng)
    print(f"Dropped: {dropped_info}")
    base_output_fp = f"{OUTPUT_DIR}/base.csv"
    base_df.to_csv(base_output_fp, index=False)
    print(f"Saved base dataset ({len(base_df)} samples) to {base_output_fp}!")

    # Dataset 2: Attempt 1
    # Duplicate samples + relabel with missing attraction_types in the Data field
    print("Generating attempt 1 dataset...")
    attempt1_df = attempt1_gen_full(base_df, dropped_info, types, rng)
    attempt1_output_fp = f"{OUTPUT_DIR}/attempt1.csv"
    attempt1_df.to_csv(attempt1_output_fp, index=False)
    print(
        f"Saved attempt 1 dataset ({len(attempt1_df)} samples) to {attempt1_output_fp}!"
    )

    # Dataset 3: Attempt 2
    # Fewshot generation for missing attraction_types
    print("Generating attempt 2 dataset (augmented part only)...")
    print("Setting up LLM for fewshot generation...")
    gen_llm = LLM(model=GEN_MODEL, tensor_parallel_size=args.num_gpus)
    gen_sampling_params = SamplingParams(
        temperature=GEN_TEMPERATURE, max_tokens=GEN_MAX_TOKENS
    )

    print("Starting fewshot generation...")
    attempt2_aug_df = attempt2_gen_aug(
        df, dropped_info, types, gen_llm, gen_sampling_params, rng
    )
    attempt2_output_fp = f"{OUTPUT_DIR}/attempt2_aug.csv"
    attempt2_aug_df.to_csv(attempt2_output_fp, index=False)
    print(
        f"Saved attempt 2 augmented dataset ({len(attempt2_aug_df)} samples) to {attempt2_output_fp}!"
        f" Run T1 inference on this dataset to get tool calls and outputs, and then concat it with the base dataset."
    )
