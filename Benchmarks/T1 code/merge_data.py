import os
import pandas as pd
import csv
import numpy as np

current_folder = os.path.dirname(os.path.abspath(__file__))

def generate_data_to_evaluate(input_path = "../data/original_raw", output_path = "../data",
                              name = "final_data.csv"):
    """Main function to merge ID, Filled_Template, Filled_Plan, and Output from CSV files into one CSV."""
    input_dir = os.path.join(current_folder, input_path)
    output_dir = os.path.join(current_folder, output_path)
    os.makedirs(output_dir, exist_ok=True)

    combined_frames = []

    def join_nonnull(s):
        return "\n".join([str(x) for x in s.dropna().astype(str) if x and x != "nan"])

    for fname in os.listdir(input_dir):
        if not fname.lower().endswith(".csv"):
            continue
        path = os.path.join(input_dir, fname)
        try:
            df = pd.read_csv(path, dtype=str)
        except (pd.errors.EmptyDataError, FileNotFoundError, PermissionError):
            continue

        if "ID" not in df.columns:
            continue

        # Keep only relevant columns if present
        cols_to_keep = ["ID", "Filled_Template", "Filled_Plan", "Output"]
        df = df.loc[:, df.columns.intersection(cols_to_keep)]
        df = df.dropna(subset=["ID"])
        df["ID"] = df["ID"].astype(str)

        agg_dict = {}
        for col in ["Filled_Template", "Filled_Plan", "Output"]:
            if col in df.columns:
                agg_dict[col] = join_nonnull

        if not agg_dict:
            continue

        grouped = df.groupby("ID", as_index=False).agg(agg_dict)
        combined_frames.append(grouped)

    if combined_frames:
        merged_all = pd.concat(combined_frames, ignore_index=True)
        # ensure column order
        cols = [c for c in ["ID", "Filled_Template", "Filled_Plan", "Output"] if c in merged_all.columns]
        rename_map = {}
        if "Filled_Template" in merged_all.columns:
            rename_map["Filled_Template"] = "Data"
        if "Filled_Plan" in merged_all.columns:
            rename_map["Filled_Plan"] = "Tool Call"
        merged_all = merged_all[cols].rename(columns=rename_map)
        merged_all.to_csv(os.path.join(output_dir, name), index=False)

    


if __name__ == "__main__":
    generate_data_to_evaluate()
