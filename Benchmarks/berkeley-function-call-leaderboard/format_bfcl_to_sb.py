import argparse
import os
import pandas as pd
from pathlib import Path

OUTPUT_ROOTDIR = "data_for_sb"


def format_question(q: list[list[str]]) -> str:
    q_parts = []
    for q_arr in q:
        for q_part in q_arr:
            if "role" in q_part and q_part["role"] == "user":
                q_parts.append(f"user: {q_part['content']}")
    return "\n".join(q_parts)


def format_tool_calls(tc: list[list[str]]) -> str:
    tc_parts = []
    for tc_arr in tc:
        for tc_single in tc_arr:
            tc_parts.append(tc_single)
    return "\n".join(tc_parts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Script to construct synthetic data in StructBench format")
    parser.add_argument("syn_path", type=str, help="Path to synthetic instructions JSON file")
    parser.add_argument("syn_tc_path", type=str, help="Path to synthetic tool calls JSON file")
    args = parser.parse_args()

    print(f"Reading synthetic instructions from {args.syn_path}")
    syn_df = pd.read_json(args.syn_path, lines=True)

    print(f"Reading synthetic tool calls from {args.syn_path}")
    syn_tc_df = pd.read_json(args.syn_tc_path, lines=True)

    syn_name = Path(args.syn_path).stem

    df = syn_df.merge(
        syn_tc_df[["id", "ground_truth"]], on="id", how="left"
    )
    df = df[["id", "question", "ground_truth"]]

    # Format question field for structbench:
    # Create a string value with user: abc lines separated by \n
    df["question"] = df["question"].apply(format_question)

    # Format ground_truth field for structbench:
    # Create a string value with each tool call separated by \n
    df["ground_truth"] = df["ground_truth"].apply(format_tool_calls)

    # Rename columns for structbench
    df.rename(columns={"id": "Id", "question": "Data", "ground_truth": "Tool Calls"}, inplace=True)

    # Save formatted file as CSV
    output_dir = f"{OUTPUT_ROOTDIR}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    output_fp = f"{output_dir}/{syn_name}_for_eval.csv"
    df.to_csv(output_fp, index=False)
    print(f"Saved formatted synthetic data to {output_fp}!")
