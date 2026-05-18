import argparse
import os
import pandas as pd
from pe.llm import HuggingfaceLLM
from inference import generate_plan
from inference import generate_output


def join_after_fmt(lines: pd.Series):
    lines = lines.dropna().astype(str)
    lines_proc = []
    for line in lines:
        if line and line not in ("nan", "\n", "", None):
            line = str(line).strip("[]\n\"")  # Remove edge characters if present
            lines_proc.append(line)
    return "\n".join([str(x) for x in lines_proc])


def format_data_for_eval(df: pd.DataFrame):
    if "ID" not in df.columns:
        return df

    # Keep only relevant columns if present
    cols_to_keep = ["ID", "Filled_Template", "Filled_Plan", "Output"]
    df = df.loc[:, df.columns.intersection(cols_to_keep)]
    df = df.dropna(subset=["ID"])
    df["ID"] = df["ID"].astype(str)

    # Aggregate multi-line values to a single value and remove unnecessary chars
    agg_dict = {}
    for col in ["Filled_Template", "Filled_Plan", "Output"]:
        if col in df.columns:
            agg_dict[col] = join_after_fmt
    if not agg_dict:
        return df
    grouped = df.groupby("ID", as_index=False).agg(agg_dict)

    # Use standard column names and column order in final dataset
    cols = [c for c in ["ID", "Filled_Template", "Filled_Plan", "Output"] if
            c in grouped.columns]
    rename_map = {}
    if "Filled_Template" in grouped.columns:
        rename_map["Filled_Template"] = "Data"
    if "Filled_Plan" in grouped.columns:
        rename_map["Filled_Plan"] = "Tool Call"
    grouped = grouped[cols].rename(columns=rename_map)

    return grouped


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to generate orig_inferred and syn_inferred")
    parser.add_argument(
        "orig_syn_abs_fp_filepath",
        type=str,
        help="Path to file with output ID and absolute filepaths for original and synthetic data"
    )
    parser.add_argument(
        "--load_orig",
        type=str,
        help="Path to precomputed orig_inferred.csv. If provided, loads instead of computing. "
             "Useful for hyperparameter sweeps that use the same orig dataset."
    )
    parser.add_argument(
        "--same_orig",
        action="store_true",
        help="Run inference on orig dataset only once. Useful for hyperparam sweeps that use the same orig dataset.")
    args = parser.parse_args()

    fps_df = pd.read_csv(args.orig_syn_abs_fp_filepath)

    llm = HuggingfaceLLM(
        max_completion_tokens=100,
        batch_size=8,
        model_name_or_path="meta-llama/Llama-3.1-8B-Instruct",
        temperature=0.5
    )

    if args.load_orig and args.same_orig:
        print(
            "Warning: Both --load_orig and --same_orig provided. Using --load_orig (--same_orig ignored).")
    elif args.load_orig:
        print(
            "--load_orig provided. Orig inferred dataset will be loaded from filepath.")
    elif args.same_orig:
        print(
            "--same_orig provided. Inference on the orig dataset will only run once.")
    else:
        print("Inference on the orig dataset will run each time.")

    orig_inferred_df = None
    if args.load_orig:
        print(f"Loading original inferred data from {args.load_orig}...")
        orig_inferred_df = pd.read_csv(args.load_orig)

    for row in fps_df.itertuples(index=False):
        output_id = row.output_id

        print(f"Starting run for {output_id=}...")
        orig_abs_path = row.orig_abs_path
        syn_abs_path = row.syn_abs_path

        output_dir = f"data/{output_id}"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        if orig_inferred_df is not None and (args.load_orig or args.same_orig):
            print("Reusing orig df...")
        else:
            print("Generating output for original data...")
            orig_df = pd.read_csv(orig_abs_path)
            orig_inferred_df = generate_output(data=orig_df, llm=llm)

        orig_out_fp = f"{output_dir}/orig_inferred.csv"
        orig_inferred_df.to_csv(orig_out_fp, index=False)
        print(f"Saved data to {orig_out_fp}")

        print("Formatting original data for evaluation...")
        orig_for_eval_df = format_data_for_eval(df=orig_inferred_df)

        orig_eval_out_fp = f"{output_dir}/orig_inferred_for_eval.csv"
        orig_for_eval_df.to_csv(orig_eval_out_fp, index=False)
        print(f"Saved data to {orig_eval_out_fp}")

        print("Generating plan and output for synthetic data...")
        syn_df = pd.read_csv(syn_abs_path)
        syn_inferred_df = generate_plan(data=syn_df, llm=llm)

        syn_out_fp = f"{output_dir}/syn_inferred.csv"
        syn_inferred_df.to_csv(syn_out_fp, index=False)
        print(f"Saved data to {syn_out_fp}")

        print("Formatting synthetic data for evaluation...")
        syn_for_eval_df = format_data_for_eval(df=syn_inferred_df)

        syn_eval_out_fp = f"{output_dir}/syn_inferred_for_eval.csv"
        syn_for_eval_df.to_csv(syn_eval_out_fp, index=False)
        print(f"Saved data to {syn_eval_out_fp}")
