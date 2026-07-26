import pandas as pd

OUTPUT_DIR = "syn_case_study"
BASE_FP = f"{OUTPUT_DIR}/base.csv"
AUG_INF_FP = f"{OUTPUT_DIR}/attempt4_aug_inferred.csv"

attempt4_output_fp = f"{OUTPUT_DIR}/attempt4.csv"

base_df = pd.read_csv(BASE_FP)
aug_inferred_df = pd.read_csv(AUG_INF_FP)
attempt4_df = pd.concat([base_df, aug_inferred_df], ignore_index=True)
attempt4_df["ID"] = list(range(len(attempt4_df)))
attempt4_df.to_csv(attempt4_output_fp, index=False)

print(f"Saved attempt 4 dataset ({len(attempt4_df)} samples) to {attempt4_output_fp}")
