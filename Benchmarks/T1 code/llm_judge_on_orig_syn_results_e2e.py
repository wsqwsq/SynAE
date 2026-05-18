import argparse
import os
import pandas as pd
import yaml
from pe.llm import HuggingfaceLLM, Request
from run_llm_on_orig_syn_bench_e2e import HfLlmConfig
from transformers import AutoTokenizer


def get_instr_to_tool_call_messages(instr: str, expected_tool_call: str, actual_tool_call: str):
    # The judge should check whether the actual_tool_call is correct for the instr, based on the expected_tool_call
    # The judge should return "yes" if the actual_tool_call is correct for the instr, and "no" if incorrect
    system_message = {
        "role": "system",
        "content": (
            "You are an evaluator. You must answer with ONLY 'yes' or 'no'. "
            "Never provide explanations or reasoning."
        ),
    }
    user_message = {
        "role": "user",
        "content": (
            f"Compare these tool call sequences for an attractions recommendation assistant:\n\n"
            f"Conversation:\n{instr}\n\n"
            f"Expected tool calls:\n{expected_tool_call}\n\n"
            f"Actual tool calls:\n{actual_tool_call}\n\n"
            f"Evaluation rules:\n"
            f"- Actual must accomplish the same goal as expected\n"
            f'- Semantic equivalence is OK (e.g., "OR" vs "Oregon", reordered operations with same result)\n'
            f"- Partial correctness = NO\n"
            f"- Different variable/cache names = OK if functionality identical\n\n"
            f"Does actual correctly implement the conversation based on expected?\n"
            f"Answer (yes/no):"
        ),
    }
    return [system_message, user_message]


def get_instr_to_tool_call_judged(expected_df: pd.DataFrame, actual_df: pd.DataFrame, llm: HuggingfaceLLM):
    print("Judging instructions <-> tool call...")
    combined_df = pd.DataFrame(
        {"instr": expected_df["Data"], "expected": expected_df["Tool Call"], "actual": actual_df["Tool Call"]}
    )
    messages_list = []
    for row in combined_df.itertuples(index=False):
        messages = get_instr_to_tool_call_messages(
            instr=row.instr, expected_tool_call=row.expected, actual_tool_call=row.actual
        )
        messages_list.append(messages)
    requests = [Request(messages=messages) for messages in messages_list]
    responses = llm.get_responses(requests)

    fixed_responses = []
    for r in responses:
        if "yes" in str(r).lower():
            fixed_responses.append("yes")
        elif "no" in str(r).lower():
            fixed_responses.append("no")
        else:
            print(r)
            fixed_responses.append("")

    return fixed_responses


def get_instr_to_output_messages(instr: str, expected_output: str, actual_output: str):
    # The judge should check whether the actual_output is correct for the instr, based on the expected_output
    # The judge should return "yes" if the actual_output is correct for the instr, and "no" if incorrect
    system_message = {
        "role": "system",
        "content": (
            "You are an evaluator. You must answer with ONLY 'yes' or 'no'. "
            "Never provide explanations or reasoning."
        ),
    }
    user_message = {
        "role": "user",
        "content": (
            f"Compare these outputs for an attractions recommendation assistant:\n\n"
            f"Conversation:\n{instr}\n\n"
            f"Expected output:\n{expected_output}\n\n"
            f"Actual output:\n{actual_output}\n\n"
            f"Evaluation rules:\n"
            f"- Actual must convey same information and meaning as expected\n"
            f"- Different wording is OK if content equivalent\n"
            f"- Partial correctness = NO\n"
            f"- Focus on semantic content, not syntax\n\n"
            f"Does actual correctly respond to the conversation based on expected?\n"
            f"Answer (yes/no):"
        ),
    }
    return [system_message, user_message]


def get_instr_to_output_judged(expected_df: pd.DataFrame, actual_df: pd.DataFrame, llm: HuggingfaceLLM):
    print("Judging instructions <-> output...")
    combined_df = pd.DataFrame(
        {"instr": expected_df["Data"], "expected": expected_df["Output"], "actual": actual_df["Output"]}
    )
    messages_list = []
    for row in combined_df.itertuples(index=False):
        messages = get_instr_to_output_messages(
            instr=row.instr, expected_output=row.expected, actual_output=row.actual
        )
        messages_list.append(messages)
    requests = [Request(messages=messages) for messages in messages_list]
    responses = llm.get_responses(requests)

    fixed_responses = []
    for r in responses:
        if "yes" in str(r).lower():
            fixed_responses.append("yes")
        elif "no" in str(r).lower():
            fixed_responses.append("no")
        else:
            print(r)
            fixed_responses.append("")

    return fixed_responses


def get_judged_df(expected_df: pd.DataFrame, actual_df: pd.DataFrame, llm: HuggingfaceLLM):
    instr_to_tool_call_res = get_instr_to_tool_call_judged(expected_df, actual_df, llm)
    instr_to_output_res = get_instr_to_output_judged(expected_df, actual_df, llm)
    res_df = actual_df.copy(deep=True)
    res_df["instr_to_tool_call_res"] = instr_to_tool_call_res
    res_df["instr_to_output_res"] = instr_to_output_res
    return res_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script to evaluate orig_llm and syn_llm using LLM-as-a-judge")
    parser.add_argument("hf_llm_config", type=str, help="Path to YAML file with HuggingfaceLLM params")
    parser.add_argument(
        "orig_syn_abs_fp_filepath",
        type=str,
        help="Path to file with output ID and absolute filepaths for original and synthetic data",
    )
    parser.add_argument(
        "model_name",
        type=str,
        help="LLM under test whose results need to be judged"
    )
    parser.add_argument(
        "--load_orig",
        type=str,
        help="Path to precomputed orig_judged.csv. If provided, loads instead of computing. "
        "Useful for hyperparameter sweeps that use the same orig dataset.",
    )
    parser.add_argument(
        "--same_orig",
        action="store_true",
        help="Judge orig_llm dataset only once. Useful for hyperparam sweeps that use the same orig dataset.",
    )
    args = parser.parse_args()

    model_name = args.model_name

    # Setup the LLM judge
    llm_config_fp = args.hf_llm_config
    with open(llm_config_fp) as stream:
        try:
            hf_llm_config = HfLlmConfig(**yaml.safe_load(stream))
            print(f"Testing LLM={model_name} with judge {hf_llm_config=} on both orig and syn benchmark data...")
        except yaml.YAMLError as exc:
            print(exc)

    tokenizer = AutoTokenizer.from_pretrained(hf_llm_config.model_name_or_path)
    llm = HuggingfaceLLM(
        model_name_or_path=hf_llm_config.model_name_or_path,
        max_completion_tokens=hf_llm_config.max_completion_tokens,
        batch_size=hf_llm_config.batch_size,
        temperature=hf_llm_config.temperature,
        tokenizer=tokenizer,
    )

    fps_df = pd.read_csv(args.orig_syn_abs_fp_filepath)
    if args.load_orig and args.same_orig:
        print("Warning: Both --load_orig and --same_orig provided. Using --load_orig (--same_orig ignored).")
    elif args.load_orig:
        print("--load_orig provided. Orig LLM results dataset will be loaded from filepath.")
    elif args.same_orig:
        print("--same_orig provided. LLM result generation on the orig dataset will only run once.")
    else:
        print("LLM result generation on the orig dataset will run each time.")

    orig_judged_df = None
    if args.load_orig:
        print(f"Loading original LLM judged data from {args.load_orig}...")
        orig_judged_df = pd.read_csv(args.load_orig)

    for row in fps_df.itertuples(index=False):
        output_id = row.output_id

        print(f"Starting run for {output_id=}...")
        output_dir = f"data/{output_id}"

        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        print("Loading original ground truth benchmark...")
        orig_expected_abs_path = f"{output_dir}/orig_inferred_for_eval.csv"
        orig_gt_df = pd.read_csv(orig_expected_abs_path)

        print("Loading synthetic ground truth benchmark...")
        syn_expected_abs_path = f"{output_dir}/syn_inferred_for_eval.csv"
        syn_gt_df = pd.read_csv(syn_expected_abs_path)

        orig_llm_outputs_abs_path = f"{output_dir}/orig_{model_name}_for_eval.csv"
        syn_llm_outputs_abs_path = f"{output_dir}/syn_{model_name}_for_eval.csv"

        if orig_judged_df is not None and (args.load_orig or args.same_orig):
            print("Reusing orig df...")
        else:
            print(f"Judging original data results for {model_name}...")
            orig_df = pd.read_csv(orig_llm_outputs_abs_path)
            orig_judged_df = get_judged_df(expected_df=orig_gt_df, actual_df=orig_df, llm=llm)

        orig_out_fp = f"{output_dir}/orig_{model_name}_for_eval_judged.csv"
        orig_judged_df.to_csv(orig_out_fp, index=False)
        print(f"Saved data to {orig_out_fp}")

        print(f"Judging synthetic data results for {model_name}...")
        syn_df = pd.read_csv(syn_llm_outputs_abs_path)
        syn_judged_df = get_judged_df(expected_df=syn_gt_df, actual_df=syn_df, llm=llm)

        syn_out_fp = f"{output_dir}/syn_{model_name}_for_eval_judged.csv"
        syn_judged_df.to_csv(syn_out_fp, index=False)
        print(f"Saved data to {syn_out_fp}")
