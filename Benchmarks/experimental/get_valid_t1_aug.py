import argparse

import pandas as pd
from vllm import LLM, SamplingParams

JUDGE_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
JUDGE_TEMPERATURE = 0.1
JUDGE_MAX_TOKENS = 10
JUDGE_TOKENIZER_MODE = "mistral"

INPUT_FP = "orig_inferred_for_eval.csv"
OUTPUT_FP = "orig_valid.csv"


def build_judge_conv(instr: str, tool_calls: str, output: str) -> list[dict]:
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
            f"Evaluate whether the system output is consistent with the instructions and tool calls for a function calling assistant:\n\n"
            f"Instructions:\n{instr}\n\n"
            f"Tool calls:\n{tool_calls}\n\n"
            f"System output (state of the system after tool calls were executed):\n{output}\n\n"
            f"Evaluation rules:\n"
            f"- System output must reflect the parameters used in the tool calls (e.g. correct city, state, attraction type)\n"
            f"- System output must be consistent with what the tool calls were meant to accomplish given the instructions\n"
            f"- Partial correctness = NO\n\n"
            f"Is the system output consistent with the instructions and tool calls?\n"
            f"Answer (yes/no):"
        ),
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
    parser = argparse.ArgumentParser(
        description="LLM-as-a-judge to filter valid T1-Augmented samples"
    )
    parser.add_argument(
        "--num-gpus", type=int, default=2, help="Number of GPUs for tensor parallelism"
    )
    args = parser.parse_args()

    # Set up vLLM judge
    judge_llm = LLM(
        model=JUDGE_MODEL,
        tokenizer_mode=JUDGE_TOKENIZER_MODE,
        config_format="mistral",
        tensor_parallel_size=args.num_gpus,
    )
    judge_sampling_params = SamplingParams(
        temperature=JUDGE_TEMPERATURE, max_tokens=JUDGE_MAX_TOKENS
    )

    print(f"Loading data from {INPUT_FP}")
    df = pd.read_csv(INPUT_FP)

    print(f"Building LLM-as-a-judge convs...")
    convs = []
    for _, row in df.iterrows():
        conv = build_judge_conv(
            instr=row["Data"],
            tool_calls=row["Tool Call"],
            output=row["Output"],
        )
        convs.append(conv)

    print(f"Running LLM-as-a-judge on {len(convs)} samples...")
    outputs = judge_llm.chat(convs, judge_sampling_params, use_tqdm=True)
    raw_responses = [output.outputs[0].text for output in outputs]
    responses = parse_responses(raw_responses)

    df["judge_response"] = responses
    valid_df = df[df["judge_response"] == "yes"].drop(columns=["judge_response"])

    print(f"Valid samples: {len(valid_df)} / {len(df)}")

    valid_df.to_csv(OUTPUT_FP, index=False)
    print(f"Saved valid samples to {OUTPUT_FP}")
