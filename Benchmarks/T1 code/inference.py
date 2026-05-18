import os
import pandas as pd
import csv
import numpy as np
import re
import warnings
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.models.auto import tokenization_auto
from tqdm.contrib.concurrent import thread_map

from t1.tools.cache import (
    get_results_from_cache,
    save_to_cache,
    reset_cache,
    dump_entire_cache,
    dump_cache_query,
    get_cache_for_current_turn,
    get_cache,
    retrieve_ground_truth_cache,
    retrieve_cache,
)

from transformers import AutoTokenizer

from t1.tools.filter_attractions import filter_attractions
from t1.tools.seek_information import seek_information
from t1.tools.filter_flights import filter_flights
from t1.tools.filter_hotels import filter_hotels
from t1.tools.filter_restaurants import filter_restaurants
from t1.tools.find_nearest import search_nearest
from t1.tools.search_attractions import search_attractions
from t1.tools.search_flights import search_flights
from t1.tools.adjust_date import adjust_date
from t1.tools.search_hotels import search_hotels
from t1.tools.search_restaurants import search_restaurants
from t1.tools.sort_results import sort_results
from t1.tools.utils.get_tool_configurations import configure_tools_definitions
from t1.planner.planner_code import (
    make_reasoning_prompt,
    get_batch_results,
    output_prompt,
)
from t1.evaluation.eval_metrics import (
    extract_tool_calls,
    count_tool_usage,
    calculate_tool_calling_metrics,
    calculate_tool_param_metrics,
)
import sacrebleu
from collections import Counter
from torchmetrics.text.bert import BERTScore

from pe.api import API
from pe.api.util import ConstantList
from pe.logging import execution_logger
from pe.data import Data
from pe.llm import Request
from pe.constant.data import TEXT_DATA_COLUMN_NAME
from pe.constant.data import LLM_REQUEST_MESSAGES_COLUMN_NAME
from pe.constant.data import LLM_PARAMETERS_COLUMN_NAME
from pe.constant.data import LABEL_ID_COLUMN_NAME
from pe.llm import HuggingfaceLLM

current_folder = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(current_folder, "../data/original_raw")


def get_eiffel_client(url="localhost:9002"):
    """Initialize and return an EiffelClient instance."""
    return EiffelClient(url=url)


def extract_code_from_generated_plan(plan: str) -> str:
    """Extract code from a generated plan."""
    if pd.isna(plan):
        return ""
    match = re.search(r"<CODE>(.*?)</CODE>", plan, re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_reasoning_from_generated_plan(plan: str) -> str:
    """Extract reasoning from a generated plan."""
    if pd.isna(plan):
        return ""
    match = re.search(r"<REASONING>(.*?)</REASONING>", plan, re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_actual_tool_calls(row: pd.Series) -> Tuple[Optional[List], Optional[Dict]]:
    """Extract actual tool calls from a row."""
    role, utterance = row["Filled_Template"].split(":", 1)
    if "assistant" in role:
        return None, None
    code = row["Filled_Plan"]
    if pd.isna(code):
        return None, None
    extracted_tool_calls = extract_tool_calls(code)
    count_tool_calls = count_tool_usage(extracted_tool_calls)
    return extracted_tool_calls, count_tool_calls


### For synthetic dataset: generate plans and final output ###
### Merge process_first_pass and generate_planner_reasoning as one function ### 
### use cache from history steps rather than ground truth ###
### use parallel execution for LLM response across samples at a certain step ###
### sequential execution for steps within a sample, as it needs cache input from history steps ###
def generate_plan(data: pd.DataFrame, llm: HuggingfaceLLM) -> pd.DataFrame:
    """
    Process the first pass: add chat_history, cache history, and error columns.
    """
    # user_turn_lists will store lists of the n-th user turn across all conversations:
    # key = 1 -> list of first user turns (one per group), key = 2 -> list of second user turns, ...
    user_turn_lists = {}

    # Group by the 'ID' column
    for event_id, group in data.groupby("ID"):
        chat_history = []
        reset_cache()
        user_count = 0  # per-group counter for user turns

        # Determine total number of user turns in this group to mark the last one
        total_user_turns = 0
        for _, r in group.iterrows():
            if pd.isna(r["Filled_Template"]):
                continue
            role_tag = r["Filled_Template"].split(":", 1)[0]
            if "user" in role_tag:
                total_user_turns += 1

        for index, row in group.iterrows():
            if pd.isna(row["Filled_Template"]):
                continue

            role, utterance = row["Filled_Template"].split(":", 1)
            if "user" in role:
                role = "user"
            elif "assistant" in role:
                role = "assistant"
            chat_history.append({role: utterance})
            row_dict = row.to_dict()
            row_dict["chat_history"] = f"{chat_history}"
            row_dict["event_id"] = event_id

            # If this is a user turn, increment per-group counter and append row_dict
            # to the corresponding global list for that nth user turn.
            if role == "user":
                user_count += 1
                # Label the last user turn
                if user_count == total_user_turns:
                    row_dict["last_user"] = True
                user_turn_lists.setdefault(user_count, []).append(row_dict)

    # Now process each user turn list to generate plans
    for user_turn, rows in user_turn_lists.items():
        # Prepare chat histories and cache states for this user turn
        chat_histories = [row["chat_history"] for row in rows]
        if user_turn > 1:
            prev_rows = user_turn_lists.get(user_turn - 1, [])
            prev_map = {r["event_id"]: r for r in prev_rows}
        else:
            prev_map = {}

        # Create prompts for this turn
        prompts = [
            make_reasoning_prompt(
                chat,
                get_cache(
                    retrieve_cache(prev_map.get(row["event_id"], {})).copy())
                if user_turn > 1 and prev_map.get(row["event_id"])
                else None,
            )
            for row, chat in zip(rows, chat_histories)
        ]

        requests = [Request(messages=messages) for messages in prompts]
        responses = llm.get_responses(requests)

        for idx, code in enumerate(responses):
            row = rows[idx]
            # Reset and build cache from previous turn (if exists)
            reset_cache()
            prev = prev_map.get(row["event_id"])
            if prev is not None:
                retrieve_cache(prev)

            # Execute current generated plan in the constructed cache context
            code_error = "success"
            code = extract_code_from_generated_plan(code)
            if code:
                try:
                    if "input" in code:
                        code_error = "generated code had input"
                        pass
                    else:
                        exec(code)
                except Exception as e:
                    code_error = str(e)

            row["cache"] = dump_entire_cache().copy()

            # Assign generated plan and execution result back to the original dataframe
            data.loc[
                (data["ID"] == row["event_id"]) &
                (data["Filled_Template"] == row["Filled_Template"]),
                "Filled_Plan"
            ] = code
            data.loc[
                (data["ID"] == row["event_id"]) &
                (data["Filled_Template"] == row["Filled_Template"]),
                "generated_code_error"
            ] = code_error

        ## Generate outputs for last-users ##
        output_rows = [r for r in rows if r.get("last_user")]
        if output_rows:
            out_prompts = [output_prompt(r["chat_history"], r["cache"]) for r in
                           output_rows]

            # Generate outputs using pe library
            requests = [Request(messages=messages) for messages in out_prompts]
            responses = llm.get_responses(requests)

            for idx, out_text in enumerate(responses):
                row = output_rows[idx]
                data.loc[
                    (data["ID"] == row["event_id"]) &
                    (data["Filled_Template"] == row["Filled_Template"]),
                    "Output",
                ] = out_text

    return data


### For original dataset: generate final outputs after plan execution ###
def generate_output(data: pd.DataFrame, llm: HuggingfaceLLM) -> pd.DataFrame:
    # Collect prompts to generate outputs across samples (parallelizable)
    out_items = []  # tuples of (event_id, filled_template, prompt)

    # Process each conversation (sequential within a conversation to keep cache updates correct)
    for event_id, group in data.groupby("ID"):
        reset_cache()
        chat_history = []
        last_user_row = None

        for _, row in group.iterrows():
            if pd.isna(row.get("Filled_Template")):
                continue

            role, utterance = row["Filled_Template"].split(":", 1)
            role = "user" if "user" in role else (
                "assistant" if "assistant" in role else role)
            chat_history.append({role: utterance})

            # Execute the Filled_Plan for this turn (if any) to update cache sequentially
            plan = row.get("Filled_Plan", "")
            code_error = "success"
            if not pd.isna(plan) and plan:
                #code = extract_code_from_generated_plan(plan)
                if plan:
                    try:
                        if "input" in plan:
                            code_error = "generated code had input"
                        else:
                            exec(plan)
                    except Exception as e:
                        code_error = str(e)

            # remember last user row for this conversation
            if role == "user":
                last_user_row = row

        # After finishing the conversation, build a prompt for the last user (if exists)
        if last_user_row is not None:
            final_cache = dump_entire_cache().copy()
            prompt = output_prompt(f"{chat_history}", final_cache)
            out_items.append(
                {
                    "event_id": event_id,
                    "filled_template": last_user_row["Filled_Template"],
                    "prompt": prompt,
                }
            )

    # Generate outputs in parallel across conversations
    if not out_items:
        return data

    requests = [Request(messages=messages) for messages in
                [it["prompt"] for it in out_items]]
    responses = llm.get_responses(requests)

    # Map generated outputs back into dataframe
    for resp_i, resp_text in enumerate(responses):
        item = out_items[resp_i]
        data.loc[
            (data["ID"] == item["event_id"]) & (
                    data["Filled_Template"] == item["filled_template"]),
            "Output",
        ] = resp_text

    return data


def process_first_pass(data: pd.DataFrame) -> pd.DataFrame:
    """
    Process the first pass: add chat_history, cache history, and error columns.
    """
    new_column_values = []

    # Group by the 'ID' column
    for event_id, group in data.groupby("ID"):
        print(f"Processing conversation ID: {event_id}")

        chat_history = []
        reset_cache()

        for index, row in group.iterrows():
            current_turn_cache = get_cache_for_current_turn()
            current_cache_full_obj = (
                dump_entire_cache().copy()
            )  # Get the full cache object, make a copy

            # Append chat history
            if pd.isna(row["Filled_Template"]):
                continue

            role, utterance = row["Filled_Template"].split(":", 1)
            if "user" in role:
                role = "user"
            elif "assistant" in role:
                role = "assistant"
            chat_history.append({role: utterance})

            # Append cache history
            ### We should not use the groud truth plan here to update the cache ###
            plan = row["Filled_Plan"]
            error = ""

            if not pd.isna(plan):
                error = "success"
                try:
                    exec(plan)
                except Exception as e:
                    error = str(e)

            row_dict = row.to_dict()
            row_dict[
                "entire_cache_before_current_turn"] = current_cache_full_obj
            row_dict["chat_history"] = f"{chat_history}"
            row_dict["cache_query_history"] = (
                dump_cache_query()
            )  # After ground truth code execution, updated cache
            row_dict["error"] = f"{error}"
            row_dict["cache_query_history_current_turn"] = (
                current_turn_cache
                # Cache just before execution of ground truth code
            )
            row_dict["cache_check"] = get_cache(current_cache_full_obj)
            row_dict["role"] = role

            new_column_values.append(row_dict)

        reset_cache()  # Reset cache after processing each conversation

    return pd.DataFrame(new_column_values)


def wrapper(kwargs):
    return get_batch_results(**kwargs)


def generate_planner_reasoning(df: pd.DataFrame):
    user_rows = df["role"] == "user"
    user_contents = df.loc[
        user_rows, ["chat_history", "cache_query_history_current_turn"]
    ]
    user_indices = df[df["role"] == "user"].index.tolist()
    df["generated_plan"] = np.nan

    # Step 3: Define the prompt creation function
    def create_prompt(df2):
        prompts = []
        for index, row in df2.iterrows():
            prompts.append(
                make_reasoning_prompt(
                    row["chat_history"], row["cache_query_history_current_turn"]
                )
            )

        return prompts

    # Step 4: Generate prompts only for user rows
    prompts = create_prompt(user_contents)
    batch_size = 1
    all_params = []
    all_batch_indices = []
    for i in range(0, len(prompts), batch_size):
        generated_code = []
        batch_prompts = prompts[i: i + batch_size]
        batch_indices = user_indices[i: i + batch_size]
        all_params.append({"prompts": batch_prompts})
        all_batch_indices.append(batch_indices)
        # code = get_batch_results(batch_prompts,tokeniser_path)
        # generated_code=[]
        # for i in code:
        #     generated_code.append(i['text_output'])
        # df.loc[batch_indices,"generated_plan"] = generated_code
    ### May need to rewrite the response handling here, maybe not? ###
    responses = thread_map(wrapper, all_params, max_workers=1)
    for i in range(len(responses)):
        code = []
        code_str = responses[i]
        code.append(code_str)
        index = all_batch_indices[i]
        for idx, val in zip(index, code):
            df.loc[idx, "generated_plan"] = val

    return df


def plan_generation():
    pass


def process_second_pass(new_data: pd.DataFrame) -> pd.DataFrame:
    """
    Process the second pass: generate plans based on chat history and cache.
    """
    new_col = []

    # Group by the 'ID' column
    for event_id, group in new_data.groupby("ID"):
        print(f"Processing conversation ID: {event_id}")

        chat_history = []

        for index, row in group.iterrows():
            planner_cache_history = retrieve_ground_truth_cache(row).copy()
            planner_cache_curr_turn = get_cache(planner_cache_history)

            # Append chat history
            if pd.isna(row["Filled_Template"]):
                continue

            role, utterance = row["Filled_Template"].split(":", 1)
            chat_history.append({role: utterance})

            # Generate plan based on role
            if "assistant" in role:
                plan = ""
                code = ""
                reasoning = ""
            elif "user" in role:
                plan = plan_generation(row["chat_history"],
                                       planner_cache_curr_turn)
                code = extract_code_from_generated_plan(plan)
                reasoning = extract_reasoning_from_generated_plan(plan)
            else:
                print(f"Unknown role: {role}")
                plan = ""
                code = ""
                reasoning = ""

            # Execute the code if it exists
            error = "success"
            if code:
                try:
                    if "input" in code:
                        error = "generated code had input"
                        pass
                    else:
                        exec(code)
                except Exception as e:
                    error = str(e)

            row_dict = row.to_dict()
            row_dict["planner_cache_curr_turn"] = planner_cache_curr_turn
            row_dict["entire_planner_cache_history"] = get_cache(
                dump_entire_cache())
            row_dict["code_error"] = error
            row_dict["generated_code"] = code
            row_dict["generated_reasoning"] = reasoning

            new_col.append(row_dict)

    return pd.DataFrame(new_col)


def process_and_save_file(file_name: str, generate='plan') -> None:
    """
    Process a single CSV file and save the results.

    Args:
        file_name: Path to the input CSV file
        generate: Whether to generate plans or output ('plan' or 'output')
    """
    print(f"\nProcessing file: {file_name}")

    # Read the CSV file
    data = pd.read_csv(file_name, sep=",", quoting=csv.QUOTE_MINIMAL, dtype=str)

    # Process first pass
    #new_data = process_first_pass(data)
    #new_data2 = generate_planner_reasoning(new_data)
    if generate == 'output':
        data = generate_output(data)
    elif generate == 'plan':
        data = generate_plan(data)
    data.to_csv(file_name, index=False)
    #print(f"Saved reasoning prompt to: {file_name}")


def main():
    """Main function to process all CSV files in a directory."""
    output_dir_root = "/workspace/outputs_geimini"
    planning_dir_root = output_dir_root
    tokeniser_path = (
        "/home/jovyan/llm-experiments-no-cache/model_zoo/simplescaling_s1.1-32B"
    )

    for domain_folder in os.listdir(INPUT_DIR):
        if domain_folder == "ontology":
            continue
        domain_path = os.path.join(INPUT_DIR, domain_folder)
        if not os.path.isdir(domain_path):
            print("No path")
            continue

        test_folder = os.path.join(domain_path, "test")
        if not os.path.isdir(test_folder):
            print("No test folder")
            continue

        # Get all CSV files in the input directory
        csv_files = [
            os.path.join(test_folder, f)
            for f in os.listdir(test_folder)
            if
            f.endswith(".csv") and os.path.isfile(os.path.join(test_folder, f))
        ]

        if not csv_files:
            print(f"No CSV files found in {INPUT_DIR}")
            return

        # Create output directories for this domain
        output_dir = os.path.join(output_dir_root, domain_folder, "test")
        planning_dir = os.path.join(planning_dir_root, domain_folder, "test")
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(planning_dir, exist_ok=True)

        # Process each CSV file
        for csv_file in csv_files:
            process_and_save_file(csv_file, generate='output')

        print(
            f"All files in test folder processed successfully for {domain_path}.")


if __name__ == "__main__":
    main()
