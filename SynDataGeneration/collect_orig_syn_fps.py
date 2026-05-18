import os
import pandas as pd
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect synthetic data filepaths")
    parser.add_argument(
        "outputs_dirpath",
        type=str,
        help="Path to the outputs directory (e.g., 'multirun/2026-01-23/15-22-23' or 'outputs/2026-01-23/15-22-23')",
    )
    parser.add_argument(
        "fext",
        default="csv",
        type=str,
        help="File extension (one of csv, json). Default = csv",
    )
    parser.add_argument(
        "--has-tool-calls",
        default=False,
        action="store_true",
        help="If passed, paths to tool calls data will be saved",
    )
    args = parser.parse_args()

    outputs_dirpath = args.outputs_dirpath

    multirun = False
    if "multirun" in outputs_dirpath:
        multirun = True

    syn_filepaths = []
    for root, dirs, files in os.walk(outputs_dirpath):
        for f in files:
            if f == f"syn_df.{args.fext}":
                syn_filepaths.append(os.path.join(root, f))

    output_id_list = []
    orig_abs_filepath_list = []
    syn_abs_filepath_list = []
    syn_tool_calls_abs_filepath_list = []
    for fp in syn_filepaths:
        # Use output_id = "date/time/run_id" for multirun/
        # and output_id = "date/time" for outputs/
        dirpath = os.path.dirname(fp)
        parts = dirpath.split(os.sep)
        if multirun:
            output_id = f"{parts[-3]}/{parts[-2]}/{parts[-1]}"
        else:
            output_id = f"{parts[-2]}/{parts[-1]}"

        syn_abs_filepath = os.path.abspath(fp)
        orig_abs_filepath = os.path.join(
            os.path.dirname(os.path.abspath(fp)), f"orig_df.{args.fext}"
        )

        output_id_list.append(output_id)
        syn_abs_filepath_list.append(syn_abs_filepath)
        orig_abs_filepath_list.append(orig_abs_filepath)

        if args.has_tool_calls:
            syn_tool_calls_abs_filepath_list.append(
                os.path.join(
                    os.path.dirname(os.path.abspath(fp)),
                    f"syn_df_tool_calls.{args.fext}",
                )
            )

    syn_abs_filepath_df = pd.DataFrame(
        {
            "output_id": output_id_list,
            "orig_abs_path": orig_abs_filepath_list,
            "syn_abs_path": syn_abs_filepath_list,
        }
    )

    if len(syn_tool_calls_abs_filepath_list) > 0:
        syn_abs_filepath_df["syn_tool_calls_abs_path"] = (
            syn_tool_calls_abs_filepath_list
        )

    out_fp = f"{outputs_dirpath}/orig_syn_abs_filepath.csv"
    syn_abs_filepath_df.to_csv(out_fp, index=False)
    print(f"Saved original and synthetic dataset filepaths to: {out_fp}!")
