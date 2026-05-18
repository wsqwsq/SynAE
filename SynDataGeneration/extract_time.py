import os
from datetime import datetime
import argparse
import pandas as pd


START_LOG_PATTERN = "Generating synthetic data from original data"
END_LOG_PATTERN = "Post-processing synthetic data"


def extract_timestamp_from_log(l):
    ts_str = l.split("][")[0][1:]  # Split by '][' and take first part, remove '['
    ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S,%f")
    return ts


def extract_timing_from_log(log_fp, unit="sec"):
    start_log_time, end_log_time = None, None
    with open(log_fp, "r") as f:
        lines = f.readlines()
        for l in lines:
            if START_LOG_PATTERN in l:
                start_log_time = extract_timestamp_from_log(l)
            elif END_LOG_PATTERN in l:
                end_log_time = extract_timestamp_from_log(l)

    timing = None
    if start_log_time and end_log_time:
        timing = end_log_time - start_log_time
        timing = timing.total_seconds()

        if unit == "min":
            timing = timing / 60
        elif unit == "hour":
            timing = timing / (60 * 60)
        elif unit == "day":
            timing = timing / (60 * 60 * 24)

    return timing


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Collect synthetic data generation times"
    )
    parser.add_argument(
        "outputs_dirpath",
        type=str,
        help="Path to the outputs directory (e.g., 'multirun/2026-01-23/15-22-23' or 'outputs/2026-01-23/15-22-23')",
    )
    parser.add_argument(
        "timing_unit",
        type=str,
        default="sec",
        help="Unit in which timing is recorded (e.g. 'sec', 'min', 'hour', or 'day')",
    )
    args = parser.parse_args()

    outputs_dirpath = args.outputs_dirpath
    timing_unit = args.timing_unit

    multirun = False
    if "multirun" in outputs_dirpath:
        multirun = True

    log_filepaths = []
    for root, dirs, files in os.walk(outputs_dirpath):
        for f in files:
            if f == "create_syn.log":
                log_filepaths.append(os.path.join(root, f))

    output_id_list = []
    timing_list = []
    for fp in log_filepaths:
        # Use output_id = "date/time/run_id" for multirun/
        # and output_id = "date/time" for outputs/
        dirpath = os.path.dirname(fp)
        parts = dirpath.split(os.sep)
        if multirun:
            output_id = f"{parts[-3]}/{parts[-2]}/{parts[-1]}"
        else:
            output_id = f"{parts[-2]}/{parts[-1]}"

        # Compute time taken to generate synthetic data
        # (exclude pre-processing original and post-processing synthetic times)
        timing = extract_timing_from_log(fp, unit=timing_unit)

        if timing:
            output_id_list.append(output_id)
            timing_list.append(timing)

    timing_df = pd.DataFrame(
        {"output_id": output_id_list, f"timing ({timing_unit})": timing_list}
    )
    out_fp = f"{outputs_dirpath}/create_syn_timing_data.csv"
    timing_df.to_csv(out_fp, index=False)
    print(f"Saved synthetic dataset generation times to: {out_fp}!")
