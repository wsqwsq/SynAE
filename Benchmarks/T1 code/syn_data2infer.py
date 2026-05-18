import os
import pandas as pd
import csv
import numpy as np
from lark import Lark

current_folder = os.path.dirname(os.path.abspath(__file__))

### -------- CFG -----------
USER = "user:"
ASSIS = "assistant:"

GRAMMAR = fr"""
    t1: preamble? conversation (conversation)*
    preamble: /(?s).+?(?={ASSIS})/
    conversation: assistant user
    assistant: "{ASSIS}" gpt_string
    user: "{USER}" user_string

    user_string: ESCAPED_STRING | /(?s).+?(?=(?:{ASSIS}|$))/
    gpt_string: ESCAPED_STRING | /(?s).+?(?=(?:{USER}|$))/

    %import common.ESCAPED_STRING
    %import common.WS
    %ignore WS
"""
### ----------------------------

parser = Lark(GRAMMAR, start="t1")

def CFG_valid(sample):
    if not isinstance(sample, str) or not sample.strip():
        return False
    try:
        parser.parse(sample)
        return True
    except Exception:
        return False
    
def parse_conversations(sample):
    parse_tree = parser.parse(sample)
    conversations = []
    for conv in parse_tree.find_data("conversation"):
        assistant_text = ""
        user_text = ""
        for child in conv.children:
            if child.data == "assistant":
                assistant_text = child.children[0].value if child.children else ""
            elif child.data == "user":
                user_text = child.children[0].value if child.children else ""
        conversations.append(ASSIS + ' ' + assistant_text.strip())
        conversations.append(USER + ' ' + user_text.strip())
    return conversations


def generate_data_to_infer(input_path, output_path):
    """Main function to merge ID, Filled_Template, Filled_Plan, and Output from CSV files into one CSV."""
    os.makedirs(output_path, exist_ok=True)

    # Read input CSV
    df = pd.read_csv(input_path)

    text_col = 'text'

    results = []
    for i, sample in enumerate(df[text_col].astype(str)):
        if not sample or pd.isna(sample) or not CFG_valid(sample):
            continue
        convs = parse_conversations(sample)
        # group as rounds: assistant + user pairs
        for c in convs:
            results.append({"ID": i, "Filled_Template": c})

    # Write output CSV
    out_path = os.path.join(output_path, "data_to_infer.csv")
    out_df = pd.DataFrame(results)
    out_df.to_csv(out_path, index=False, quoting=csv.QUOTE_MINIMAL)
