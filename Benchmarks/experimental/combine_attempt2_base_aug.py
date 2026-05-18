import pandas as pd

OUTPUT_DIR = "syn_case_study"
BASE_FP = f"{OUTPUT_DIR}/base.csv"
AUG_INF_FP = f"{OUTPUT_DIR}/attempt2_aug_inferred.csv"

attempt2_output_fp = f"{OUTPUT_DIR}/attempt2.csv"

base_df = pd.read_csv(BASE_FP)
aug_inferred_df = pd.read_csv(AUG_INF_FP)
attempt2_df = pd.concat([base_df, aug_inferred_df], ignore_index=True)
attempt2_df["ID"] = list(range(len(attempt2_df)))

print(f"Saved attempt 2 dataset ({len(attempt2_df)} samples) to {attempt2_output_fp}")
