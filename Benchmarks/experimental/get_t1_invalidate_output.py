import os
import re

import numpy as np
import pandas as pd

INPUT_FP = "orig_valid.csv"
OUTPUT_DIR = "syn_invalidate_out"
ONTOLOGY_FP = "ontology_t1_attraction_data.csv"
INVALIDATE_FRACS = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
SEED = 123


def extract_types_from_tc(tc: str) -> list[str]:
    match = re.search(r"type=\[([^\]]*)\]", tc)
    if not match:
        return []
    return re.findall(r'"([^"]+)"', match.group(1))


def invalidate_output(
    output: str, current_types: list[str], valid_types: list, rng
) -> str:
    """Invalidates Output by replacing attraction_type with a different valid one."""
    for current_type in current_types:
        new_type = rng.choice([t for t in valid_types if t != current_type])
        output = re.sub(
            r"\b" + re.escape(current_type) + r"\b",
            new_type,
            output,
            flags=re.IGNORECASE,
        )
    return output


def invalidate_gen(
    df: pd.DataFrame, frac: float, valid_types: list, rng
) -> pd.DataFrame:
    n_total = len(df)
    invalid_positions = rng.choice(n_total, size=int(frac * n_total), replace=False)

    syn_df = df.copy().reset_index(drop=True)
    for pos in invalid_positions:
        current_types = extract_types_from_tc(syn_df.at[pos, "Tool Call"])
        if current_types:
            syn_df.at[pos, "Output"] = invalidate_output(
                syn_df.at[pos, "Output"], current_types, valid_types, rng
            )
    return syn_df


if __name__ == "__main__":
    print(f"Loading data from {INPUT_FP}")
    df = pd.read_csv(INPUT_FP)

    print(f"Loading T1 attraction ontology from {ONTOLOGY_FP}")
    ontology_df = pd.read_csv(ONTOLOGY_FP)
    valid_types = sorted(ontology_df["type"].unique().tolist())

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for frac in INVALIDATE_FRACS:
        print(f"Invalidating outputs for {frac=} of all samples...")
        rng = np.random.default_rng(SEED)
        syn_df = invalidate_gen(df, frac, valid_types, rng)

        frac_str = str(frac).replace(".", "_")
        output_fp = f"{OUTPUT_DIR}/invalidate_frac{frac_str}.csv"
        syn_df.to_csv(output_fp, index=False)

        n_invalid = int(frac * len(df))
        print(f"Saved data with {n_invalid} invalid samples to {output_fp}!")
