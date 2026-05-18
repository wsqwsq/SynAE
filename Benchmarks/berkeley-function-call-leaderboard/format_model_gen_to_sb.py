import argparse
import json
import os
import pandas as pd


OUTPUT_ROOTDIR = "data_for_llm_judge"


def format_question(q: list[list[str]]) -> str:
    q_parts = []
    for q_arr in q:
        for q_part in q_arr:
            if "role" in q_part and q_part["role"] == "user":
                q_parts.append(f"user: {q_part['content']}")
    return "\n".join(q_parts)


def format_tool_calls(tc: list[list[str]]) -> str:
    tc_parts = []
    for tc_arr in tc:
        for tc_single in tc_arr:
            tc_parts.append(tc_single)
    return "\n".join(tc_parts)


def load_score_file(file_path: str):
    result = []
    with open(file_path) as f:
        for line in f.readlines():
            json_line = json.loads(line)
            if "accuracy" not in json_line:
                result.append(json_line)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Format LLM-generated tool calls for LLM judge evaluation")
    parser.add_argument("--model", required=True, help="Model name (e.g. meta-llama/Llama-3.1-8B-Instruct)")
    parser.add_argument("--test-category", required=True, help="Test category (e.g. blankfill_prob0_1)")
    parser.add_argument("--score-dir", default="score", help="Path to score directory")
    parser.add_argument("--data-dir", default="bfcl_eval/data", help="Path to benchmark data directory")
    args = parser.parse_args()

    model_dir = args.model.replace("/", "_")
    score_fp = f"{args.score_dir}/{model_dir}/multi_turn/BFCL_v4_{args.test_category}_score.json"
    instructions_fp = f"{args.data_dir}/BFCL_v4_{args.test_category}.json"

    print(f"Reading score file from {score_fp}")
    score_data = load_score_file(score_fp)

    print(f"Reading instructions from {instructions_fp}")
    instructions_df = pd.read_json(instructions_fp, lines=True)

    # Extract questions from instructions_df
    question_list = instructions_df["question"].apply(format_question)

    # Extract generated tool calls from score_data
    tool_calls_list = []
    for res in score_data:
        res_id = res["id"]
        res_tool_calls = res.get("model_result_decoded", [])
        flattened_tool_calls = []
        for turn_steps in res_tool_calls:
            turn_calls = []
            for step_calls in turn_steps:
                turn_calls.extend(step_calls)
            if len(turn_calls) > 0:
                flattened_tool_calls.append(turn_calls)
        tool_calls_list.append(flattened_tool_calls)
    tool_calls_list = [format_tool_calls(tc) for tc in tool_calls_list]

    df = pd.DataFrame({
        "Id": instructions_df["id"],
        "Data": question_list,
        "Tool Calls": tool_calls_list
    })

    output_dir = f"{OUTPUT_ROOTDIR}/{model_dir}"
    os.makedirs(output_dir, exist_ok=True)
    output_fp = f"{output_dir}/BFCL_v4_{args.test_category}_llm_gen.csv"

    df.to_csv(output_fp, index=False)
    print(f"Saved to {output_fp}!")
