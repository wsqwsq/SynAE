import argparse
import os

import pandas as pd
from vllm import LLM, SamplingParams

JUDGE_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
JUDGE_TEMPERATURE = 0.1
JUDGE_MAX_TOKENS = 10
JUDGE_TOKENIZER_MODE = "mistral"

DATA_FOR_SB_DIR = "data_for_sb"
DATA_FOR_LLM_JUDGE_DIR = "data_for_llm_judge"


def build_judge_conv(instr: str, expected_tool_calls: str, actual_tool_calls: str) -> list[dict]:
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
            f"Compare these outputs for a function calling assistant:\n\n"
            f"User Requests:\n{instr}\n\n"
            f"Expected tool calls:\n{expected_tool_calls}\n\n"
            f"Actual tool calls:\n{actual_tool_calls}\n\n"
            f"Evaluation rules:\n"
            f"- Actual must accomplish the same goal as expected\n"
            f'- Semantic equivalence is OK (e.g., reordered operations with same result)\n'
            f"- Partial correctness = NO\n"
            f"- Different variable names = OK if functionality identical\n\n"
            f"Does actual correctly implement the user requests based on expected?\n"
            f"Answer (yes/no):"
        )
    }

    return [system_message, user_message]


def parse_responses(responses: list[str]) -> list[str]:
    fixed = []
    for r in responses:
        if "yes" in r.lower():
            fixed.append("yes")
        elif "no" in r.lower():
            fixed.append("no")
        else:
            print(f"Unexpected judge response: {r!r}")
            fixed.append("")
    return fixed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM-as-a-judge for BFCL tool call evaluation")
    parser.add_argument("--model", required=True, help="Model under test (e.g. meta-llama/Llama-3.1-8B-Instruct)")
    parser.add_argument("--test-categories", nargs="+", required=True, help="One or more test categories")
    parser.add_argument("--num-gpus", type=int, default=2, help="Number of GPUs for tensor parallelism")
    args = parser.parse_args()

    model_dir = args.model.replace("/", "_")

    # Set up vLLM judge
    judge_llm = LLM(model=JUDGE_MODEL, tokenizer_mode=JUDGE_TOKENIZER_MODE, config_format="mistral", tensor_parallel_size=args.num_gpus)
    judge_sampling_params = SamplingParams(temperature=JUDGE_TEMPERATURE, max_tokens=JUDGE_MAX_TOKENS)

    # Build conv for test category and run judge
    for test_category in args.test_categories:
        print(f"Judging {test_category}...")

        gt_fp = f"{DATA_FOR_SB_DIR}/BFCL_v4_{test_category}_for_eval.csv"
        llm_gen_fp = f"{DATA_FOR_LLM_JUDGE_DIR}/{model_dir}/BFCL_v4_{test_category}_llm_gen.csv"

        print(f"Loading ground truth from {gt_fp}")
        expected_df = pd.read_csv(gt_fp)

        print(f"Loading LLM generated data from {llm_gen_fp}")
        actual_df = pd.read_csv(llm_gen_fp)

        combined_df = pd.DataFrame({
            "instr": expected_df["Data"],
            "expected": expected_df["Tool Calls"],
            "actual": actual_df["Tool Calls"]
        })

        print(f"Building LLM-as-a-judge convs...")
        convs = []
        for row in combined_df.itertuples():
            conv = build_judge_conv(
                instr=row.instr,
                expected_tool_calls=row.expected,
                actual_tool_calls=row.actual
            )
            convs.append(conv)

        print(f"Running LLM-as-a-judge...")
        outputs = judge_llm.chat(convs, judge_sampling_params, use_tqdm=True)
        raw_responses = []
        for output in outputs:
            generated_text = output.outputs[0].text
            raw_responses.append(generated_text)
        responses = parse_responses(raw_responses)

        res_df = actual_df.copy(deep=True)
        res_df["instr_to_tool_call_res"] = responses

        output_dir = f"{DATA_FOR_LLM_JUDGE_DIR}/{model_dir}"
        output_fp = f"{output_dir}/BFCL_v4_{test_category}_llm_gen_judged.csv"
        os.makedirs(output_dir, exist_ok=True)

        res_df.to_csv(output_fp, index=False)
        print(f"Saved judged results to {output_fp}")

