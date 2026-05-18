import argparse

import pandas as pd

OUTPUT_DIR = "syn_case_study"
BASE_FP = f"{OUTPUT_DIR}/base.csv"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Combine base and attempt 3 augmented datasets")
    parser.add_argument("--aug-inferred", type=str, required=True, help="Path to the inferred augmented CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to save the combined output CSV")
    args = parser.parse_args()

    base_df = pd.read_csv(BASE_FP)
    aug_inferred_df = pd.read_csv(args.aug_inferred)
    attempt3_df = pd.concat([base_df, aug_inferred_df], ignore_index=True)
    attempt3_df["ID"] = list(range(len(attempt3_df)))
    attempt3_df.to_csv(args.output, index=False)
    print(f"Saved attempt 3 dataset ({len(attempt3_df)} samples) to {args.output}")
