import argparse
import re
import os
from pathlib import Path
from typing import Literal, Optional

import pandas as pd

from benchmarks.t1_attraction import preprocess
from config import BenchmarkType


def classify_t1_attraction_syn(df: pd.DataFrame):
    df = preprocess(df)
    ONTOLOGY_FP = "orig_data/t1/attraction_train/ontology_t1_attraction_data.csv"
    ontology_df = pd.read_csv(ONTOLOGY_FP)

    types = ontology_df["type"].unique()
    cities = ontology_df["city"].unique()
    states = ontology_df["state"].unique()

    def get_type(filled_tmpl: str) -> str:
        for t in types:
            if re.search(rf"\b{re.escape(t)}\b", filled_tmpl):
                return t
        return None

    def get_city(filled_tmpl: str) -> str:
        for c in cities:
            if re.search(rf"\b{re.escape(c)}\b", filled_tmpl):
                return c
        return None

    def get_state(filled_tmpl: str) -> str:
        for s in states:
            if re.search(rf"\b{re.escape(s)}\b", filled_tmpl):
                return s
        return None

    type_list = df["Filled_Template"].apply(get_type)
    city_list = df["Filled_Template"].apply(get_city)
    state_list = df["Filled_Template"].apply(get_state)

    class_df = pd.DataFrame(
        {
            "ID": df["ID"],
            "Type": type_list,
            "City": city_list,
            "State": state_list,
        }
    )
    return class_df


def classify_bfcl_multiturn_base_syn(df: pd.DataFrame):
    # These are taken from https://gorilla.cs.berkeley.edu/blogs/13_bfcl_v3_multi_turn.html#composition
    PRIMARY_APIS = ["GorillaFileSystem", "TradingBot", "TravelAPI", "VehicleControlAPI"]
    SECONDARY_APIS = ["TicketAPI", "TwitterAPI", "MessageAPI", "MathAPI"]

    # No reference, came up with this by looking at the available tools
    RISKY_API_FUNCS = [
        "GorillaFileSystem.rm",
        "GorillaFileSystem.rmdir",
        "TradingBot.cancel_order",
        "TradingBot.withdraw_funds",
        "TradingBot.remove_stock_from_watchlist",
        "TravelAPI.cancel_booking",
    ]

    def get_api(classes: list[str], api_list: list[str]) -> str:
        for p in api_list:
            if p in classes:
                return p
        return None

    def get_conv_len(q: list) -> Literal["short", "medium", "long"]:
        conv_len = len(q)
        if conv_len <= 2:
            return "short"
        elif 3 <= conv_len <= 5:
            return "medium"
        else:
            return "long"

    def get_has_risky_func(funcs) -> bool:
        for f in funcs:
            if f in RISKY_API_FUNCS:
                return True
        return False

    primary_api_list = df["involved_classes"].apply(lambda x: get_api(x, PRIMARY_APIS))
    secondary_api_list = df["involved_classes"].apply(
        lambda x: get_api(x, SECONDARY_APIS)
    )
    conv_len_list = df["question"].apply(get_conv_len)
    has_risky_api_list = df["path"].apply(get_has_risky_func)

    class_df = pd.DataFrame(
        {
            "id": df["id"],
            "primary_api": primary_api_list,
            "secondary_api": secondary_api_list,
            "conv_len": conv_len_list,
            "has_risky_state_update_api": has_risky_api_list,
        }
    )
    return class_df


def classify_acp_app_prog_syn(df: pd.DataFrame):
    def get_domain(context: str) -> Optional[None]:
        if "ferry domain" in context:
            return "ferry"
        elif "several cities" in context:
            return "logistics"
        elif "blocksworld domain" in context:
            return "blocksworld"
        elif "robot is in a grid" in context:
            return "grid"
        elif "set of robots" in context:
            return "floortile"
        elif "grippers domain" in context:
            return "grippers"
        elif "Rovers domain" in context:
            return "rovers"
        elif "visitall domain" in context:
            return "visitall"
        elif "depot domain" in context:
            return "depot"
        elif "robotic arm is in a grid" in context:
            return "goldminer"
        elif "satellite(s)" in context:
            return "satellite"
        elif "swap domain" in context:
            return "swap"
        elif "alfworld domain" in context:
            return "alfworld"
        else:
            return None

    domain_list = df["context"].apply(get_domain)

    class_df = pd.DataFrame(
        {
            "id": df["id"],
            "type": df["group"],
            "domain": domain_list,
        }
    )
    return class_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect synthetic data filepaths")
    parser.add_argument(
        "outputs_dirpath",
        type=str,
        help="Path to the outputs directory (e.g., 'multirun/2026-01-23/15-22-23' or 'outputs/2026-01-23/15-22-23')",
    )
    parser.add_argument(
        "--fext",
        default="csv",
        type=str,
        help="File extension (one of csv, json). Default = csv",
    )
    parser.add_argument(
        "--benchmark_type",
        default="t1_attraction",
        type=str,
        help="Benchmark type (one of t1_attraction, bfcl_multiturn_base, acp_app_prog). Default = t1_attraction",
    )
    args = parser.parse_args()

    outputs_dirpath = args.outputs_dirpath

    multirun = False
    if "multirun" in outputs_dirpath:
        multirun = True

    syn_proc_filepaths = []
    for root, dirs, files in os.walk(outputs_dirpath):
        for f in files:
            if f == f"syn_df_proc.{args.fext}":
                syn_proc_filepaths.append(os.path.join(root, f))

    benchmark_type = args.benchmark_type

    for syn_fp in syn_proc_filepaths:
        print(f"Classifying synthetic data from {syn_fp}...")

        save_dir = Path(syn_fp).parent
        output_fp = f"{save_dir}/syn_df_class.csv"

        # Load and classify syn proc df according to benchmark type
        if benchmark_type == BenchmarkType.T1_ATTRACTION.value:
            syn_proc_df = pd.read_csv(syn_fp)
            class_df = classify_t1_attraction_syn(syn_proc_df)
            class_df.to_csv(output_fp, index=False)
        elif benchmark_type == BenchmarkType.BFCL_MULTITURN_BASE.value:
            syn_proc_df = pd.read_json(syn_fp, lines=True)
            class_df = classify_bfcl_multiturn_base_syn(syn_proc_df)
            class_df.to_csv(output_fp, index=False)
        elif benchmark_type == BenchmarkType.ACP_APP_PROG.value:
            syn_proc_df = pd.read_csv(syn_fp)
            class_df = classify_acp_app_prog_syn(syn_proc_df)
            class_df.to_csv(output_fp, index=False)
        else:
            raise ValueError(f"Benchmark type: {benchmark_type} not supported!")

        print(f"Saved classification to {output_fp}!")
