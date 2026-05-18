import os
import pandas as pd
import csv
import numpy as np

current_folder = os.path.dirname(os.path.abspath(__file__))

def main():
    """Main function to merge ID, Filled_Template, Filled_Plan, and Output from CSV files into one CSV."""
    input_dir = os.path.join(current_folder, "../data/original_raw")
    output_dir = os.path.join(current_folder, "../data")
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
        cols_to_keep = ["ID", "Filled_Template"]
        df = df.loc[:, df.columns.intersection(cols_to_keep)]
        df = df.dropna(subset=["ID"])
        df["ID"] = df["ID"].astype(str)

        agg_dict = {"Filled_Template": join_nonnull}

        grouped = df.groupby("ID", as_index=False).agg(agg_dict)
        combined_frames.append(grouped)

    if combined_frames:
        merged_all = pd.concat(combined_frames, ignore_index=True)
        rename_map = {"Filled_Template": "text"}
        merged_all = merged_all["Filled_Template"].rename(columns=rename_map)
        merged_all.to_csv(os.path.join(output_dir, "ori_data.csv"), index=False)



if __name__ == "__main__":
    main()
