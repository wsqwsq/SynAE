import sys
from pathlib import Path
from typing import Literal

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

HERE = Path(__file__).parent
ORIG_DF_FP = HERE / "multiturn_base/BFCL_v4_multi_turn_base_instr.json"
ORIG_TC_DF_FP = HERE / "multiturn_base/BFCL_v4_multi_turn_base_tool_calls.json"

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

orig_df = pd.read_json(ORIG_DF_FP, lines=True)
orig_tc_df = pd.read_json(ORIG_TC_DF_FP, lines=True)


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


def get_n_tc(tc: list) -> Literal["low", "medium", "high"]:
    tc_list = []
    for turn_tc in tc:
        for step_tc in turn_tc:
            tc_list.append(step_tc)
    n_tc = len(tc_list)
    if n_tc <= 4:
        return "low"
    elif 5 <= n_tc <= 7:
        return "medium"
    else:
        return "high"


def get_max_tc_per_turn(tc) -> Literal["low", "medium", "high"]:
    tc_lens = [len(x) for x in tc]
    max_tc = max(tc_lens)
    if max_tc <= 2:
        return "low"
    elif 3 <= max_tc <= 5:
        return "medium"
    else:
        return "high"


def get_has_risky_func(funcs) -> bool:
    for f in funcs:
        if f in RISKY_API_FUNCS:
            return True
    return False


primary_api_list = orig_df["involved_classes"].apply(lambda x: get_api(x, PRIMARY_APIS))
secondary_api_list = orig_df["involved_classes"].apply(
    lambda x: get_api(x, SECONDARY_APIS)
)
conv_len_list = orig_df["question"].apply(get_conv_len)
n_tc_list = orig_tc_df["ground_truth"].apply(get_n_tc)
max_tc_per_turn_list = orig_tc_df["ground_truth"].apply(get_max_tc_per_turn)
has_risky_api_list = orig_df["path"].apply(get_has_risky_func)


class_df = pd.DataFrame(
    {
        "id": orig_df["id"],
        "primary_api": primary_api_list,
        "secondary_api": secondary_api_list,
        "conv_len": conv_len_list,
        "n_tool_calls": n_tc_list,
        "max_tool_calls_per_turn": max_tc_per_turn_list,
        "has_risky_state_update_api": has_risky_api_list,
    }
)

output_fp = HERE / "multiturn_base/classification.csv"
class_df.to_csv(output_fp, index=False)
print(f"Saved classification data to {output_fp}!")
