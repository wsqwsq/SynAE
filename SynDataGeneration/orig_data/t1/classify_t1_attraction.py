import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from benchmarks.t1_attraction import load, preprocess

HERE = Path(__file__).parent
T1_SPLIT_MAX = 15
T1_FPS = [
    HERE / f"attraction_train/output_file_attraction_train_{i}.csv"
    for i in range(1, T1_SPLIT_MAX + 1)
]
ONTOLOGY_FP = HERE / "attraction_train/ontology_t1_attraction_data.csv"

orig_df = load(filepaths=T1_FPS)
pre_orig_df = preprocess(df=orig_df)
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


type_list = pre_orig_df["Filled_Template"].apply(get_type)
city_list = pre_orig_df["Filled_Template"].apply(get_city)
state_list = pre_orig_df["Filled_Template"].apply(get_state)

class_df = pd.DataFrame(
    {
        "ID": pre_orig_df["ID"],
        "Type": type_list,
        "City": city_list,
        "State": state_list,
    }
)

output_fp = HERE / "attraction_train/classification.csv"
class_df.to_csv(output_fp, index=False)
print(f"Saved classification data to {output_fp}!")
