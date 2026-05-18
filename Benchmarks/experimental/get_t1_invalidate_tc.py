import os
import re

import numpy as np
import pandas as pd

INPUT_FP = "orig_valid.csv"
OUTPUT_DIR = "syn_invalidate_tc"
ONTOLOGY_FP = "ontology_t1_attraction_data.csv"
INVALIDATE_FRACS = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
SEED = 123


def invalidate_tool_call(
    tc: str, valid_states: list, valid_cities: list, valid_types: list, rng
) -> str:
    """Invalidates Tool Calls by replacing existing city, state, and/or
    attraction_type with different valid ones."""
    state_match = re.search(r'state="([^"]*)"', tc)
    if state_match:
        other_states = [s for s in valid_states if s != state_match.group(1)]
        tc = re.sub(r'state="[^"]*"', f'state="{rng.choice(other_states)}"', tc)

    city_match = re.search(r'city="([^"]*)"', tc)
    if city_match:
        other_cities = [c for c in valid_cities if c != city_match.group(1)]
        tc = re.sub(r'city="[^"]*"', f'city="{rng.choice(other_cities)}"', tc)

    type_match = re.search(r"type=\[([^\]]*)\]", tc)
    if type_match:
        current_types = re.findall(r'"([^"]+)"', type_match.group(1))
        new_types_list = []
        for ct in current_types:
            other_types = [t for t in valid_types if t != ct]
            new_types_list.append(f'"{rng.choice(other_types)}"')
        tc = re.sub(r"type=\[[^\]]*\]", f"type=[{', '.join(new_types_list)}]", tc)

    return tc


def invalidate_gen(
    df: pd.DataFrame,
    frac: float,
    valid_states: list,
    valid_cities: list,
    valid_types: list,
    rng,
) -> pd.DataFrame:
    n_total = len(df)
    invalid_positions = rng.choice(n_total, size=int(frac * n_total), replace=False)

    syn_df = df.copy().reset_index(drop=True)
    for pos in invalid_positions:
        syn_df.at[pos, "Tool Call"] = invalidate_tool_call(
            syn_df.at[pos, "Tool Call"], valid_states, valid_cities, valid_types, rng
        )
    return syn_df


if __name__ == "__main__":
    print(f"Loading data from {INPUT_FP}")
    df = pd.read_csv(INPUT_FP)

    print(f"Loading T1 attraction ontology from {ONTOLOGY_FP}")
    ontology_df = pd.read_csv(ONTOLOGY_FP)
    valid_states = sorted(ontology_df["state"].unique().tolist())
    valid_cities = sorted(ontology_df["city"].unique().tolist())
    valid_types = sorted(ontology_df["type"].unique().tolist())

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for frac in INVALIDATE_FRACS:
        print(f"Invalidating tool calls for {frac=} of all samples...")

        rng = np.random.default_rng(SEED)
        syn_df = invalidate_gen(df, frac, valid_states, valid_cities, valid_types, rng)

        frac_str = str(frac).replace(".", "_")
        output_fp = f"{OUTPUT_DIR}/invalidate_frac{frac_str}.csv"
        syn_df.to_csv(output_fp, index=False)

        n_invalid = int(frac * len(df))
        print(f"Saved data with {n_invalid} invalid samples to {output_fp}!")
