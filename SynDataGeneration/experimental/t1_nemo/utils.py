import pandas as pd
from typing import Literal
from pydantic import BaseModel, Field
import yaml

DEFAULT_CONFIG_PATH = "model_configs/model/default.yaml"


def load_model_config(config_path: str) -> dict:
    with open(DEFAULT_CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)
    if config_path:
        with open(config_path) as f:
            cfg.update(yaml.safe_load(f))
    return cfg


class Message(BaseModel):
    """A single message turn in the conversation."""

    role: Literal["user", "assistant"] = Field(
        ..., description="Which role is writing the message."
    )
    content: str = Field(..., description="Message contents.")


class ChatConversation(BaseModel):
    """A chat conversation between a user and a travel AI assistant.
    All conversations are initiated by the assistant role.
    Turns alternate between user and assistant roles.
    The last message is always from the user role.
    Message content can be long or short.
    The conversation should have 6 turns.
    """

    conversation: list[Message] = Field(
        ..., description="List of all messages in the conversation."
    )


def load(filepaths: list[str]):
    orig_df_chunks = []
    i_chunk = 0
    for df_fp in filepaths:
        df = pd.read_csv(df_fp)
        for g_name, g_df in df.groupby("ID"):
            corrected_id_df = pd.DataFrame(
                {
                    "ID": [i_chunk] * len(g_df),
                    "Template": g_df["Template"],
                    "Plan": g_df["Plan"],
                    "Filled_Template": g_df["Filled_Template"],
                    "Filled_Plan": g_df["Filled_Plan"],
                }
            )
            orig_df_chunks.append(corrected_id_df)
            i_chunk += 1
    orig_df = pd.concat(orig_df_chunks)
    return orig_df


def preprocess(df: pd.DataFrame):
    orig_df_proc = (
        df[["ID", "Filled_Template"]]
        .groupby("ID")
        .agg(lambda x: "\n".join(x))
        .reset_index()
    )
    return orig_df_proc


def get_valid_lines(conv: str) -> list[str]:
    lines = conv.split("\n")

    # Remove empty lines
    # Remove lines that don't start with user: or assistant:
    valid_lines = []
    for ln in lines:
        if ln.strip() not in (None, "", "\n"):
            if ln.lower().startswith("user:") or ln.lower().startswith("assistant:"):
                valid_lines.append(ln)

    return valid_lines


def postprocess(df: pd.DataFrame):
    syn_ids_list = []
    syn_conv_lines_list = []
    for i, syn_conv in enumerate(df["Filled_Template"]):
        fixed_syn_conv_lines = get_valid_lines(str(syn_conv))
        syn_ids_list.extend([i] * len(fixed_syn_conv_lines))
        syn_conv_lines_list.extend(fixed_syn_conv_lines)

    syn_df = pd.DataFrame({"ID": syn_ids_list, "Filled_Template": syn_conv_lines_list})
    return syn_df, None


def save(df: pd.DataFrame, fn: str):
    fp = f"{fn}.csv"
    df.to_csv(fp, index=False)
    print(f"Saved data to {fp}!")


def get_t1_attraction_ontology():
    df = pd.read_csv("ontology_t1_attraction_data.csv")
    return {"states": df["state"].unique(), "types": df["type"].unique()}
