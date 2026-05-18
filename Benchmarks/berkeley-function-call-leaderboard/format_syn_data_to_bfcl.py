import argparse
import pandas as pd

OUTPUT_DIR = "bfcl_eval/data"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to format and save synthetic data for running BFCL")
    parser.add_argument(
        "orig_syn_abs_fp_filepath",
        type=str,
        help="Path to file with output ID and absolute filepaths for original and synthetic data"
    )
    args = parser.parse_args()

    fps_df = pd.read_csv(args.orig_syn_abs_fp_filepath)

    for row in fps_df.itertuples():
        syn_fp = row.syn_abs_path
        syn_df = pd.read_json(syn_fp, lines=True)
        test_category_name = str(syn_df["id"].iloc[0]).rsplit("_", 1)[0]
        syn_df.to_json(
            f"{OUTPUT_DIR}/BFCL_v4_{test_category_name}.json",
            orient="records",
            lines=True
        )

        if row.syn_tool_calls_abs_path:
            syn_tool_calls_fp = row.syn_tool_calls_abs_path
            syn_tool_calls_df = pd.read_json(syn_tool_calls_fp, lines=True)
            syn_tool_calls_df.rename(columns={"tool_calls": "ground_truth"}, inplace=True)
            syn_tool_calls_df.to_json(
                f"{OUTPUT_DIR}/possible_answer/BFCL_v4_{test_category_name}.json",
                orient="records",
                lines=True
            )
