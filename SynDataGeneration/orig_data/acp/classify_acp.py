import sys
from pathlib import Path
from typing import Literal, Optional

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

HERE = Path(__file__).parent
ORIG_DF_FP = HERE / "acp_app_prog.csv"
orig_df = pd.read_csv(ORIG_DF_FP)


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


domain_list = orig_df["context"].apply(get_domain)

class_df = pd.DataFrame(
    {
        "id": orig_df["id"],
        "type": orig_df["group"],
        "domain": domain_list,
    }
)

output_fp = HERE / "classification.csv"
class_df.to_csv(output_fp, index=False)
print(f"Saved classification data to {output_fp}!")
