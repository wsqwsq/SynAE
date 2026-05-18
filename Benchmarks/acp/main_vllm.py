import argparse
import os
import re
from dataclasses import dataclass

import pandas as pd
import yaml
from vllm import LLM, SamplingParams


@dataclass
class VllmConfig:
    model_name_or_path: str
    max_completion_tokens: int
    temperature: float


# Source: https://github.com/IBM/ACPBench/blob/main/evals/acpbench.py
BOOLEAN_TEMPLATE = """{context}
{prompt}
Only answer yes or no."""

BOOLEAN_REGEX = r"\b(yes|no)\b"


def format_data(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Data": df.apply(
                lambda r: BOOLEAN_TEMPLATE.format(
                    context=r["context"], prompt=r["question"]
                ),
                axis=1,
            ),
            "Output": df["answer"],
        }
    )


def build_conv(context: str, question: str) -> list[dict]:
    return [
        {
            "role": "user",
            "content": BOOLEAN_TEMPLATE.format(context=context, prompt=question),
        }
    ]


def parse_responses(responses: list[str]) -> list[str]:
    parsed = []
    for r in responses:
        m = re.search(BOOLEAN_REGEX, r.lower())
        if m:
            parsed.append(m.group(0))
        else:
            print(f"Unexpected response: {r!r}")
            parsed.append("")
    return parsed


def run_eval(
    df: pd.DataFrame, llm: LLM, sampling_params: SamplingParams
) -> pd.DataFrame:
    convs = [build_conv(row.context, row.question) for row in df.itertuples()]
    outputs = llm.chat(convs, sampling_params, use_tqdm=True)
    raw_responses = [o.outputs[0].text for o in outputs]
    predictions = parse_responses(raw_responses)

    result_df = df.copy(deep=True)
    result_df["prediction"] = predictions
    result_df["correct"] = result_df["prediction"] == result_df["answer"].str.lower()
    return result_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to run ACP benchmarks on LLMs using vLLM offline inference"
    )
    parser.add_argument(
        "vllm_config", type=str, help="Path to YAML file with vllm LLM params"
    )
    parser.add_argument(
        "orig_syn_abs_fp_filepath",
        type=str,
        help="Path to file with output ID and absolute filepaths for original and synthetic data",
    )
    parser.add_argument("syn_gen_method", type=str, help="Name of syn gen method")
    parser.add_argument(
        "--num-gpus", type=int, default=2, help="Number of GPUs for tensor parallelism"
    )
    parser.add_argument(
        "--load-orig",
        type=str,
        help="Path to precomputed orig_results.csv. If provided, skips running the LLM on the original benchmark.",
    )
    args = parser.parse_args()

    with open(args.vllm_config) as f:
        vllm_config = VllmConfig(**yaml.safe_load(f))
    print(f"Testing LLM with {vllm_config=} on both orig and syn benchmark data...")

    llm = LLM(model=vllm_config.model_name_or_path, tensor_parallel_size=args.num_gpus)
    sampling_params = SamplingParams(
        temperature=vllm_config.temperature,
        max_tokens=vllm_config.max_completion_tokens,
    )

    fps_df = pd.read_csv(args.orig_syn_abs_fp_filepath)

    model_str = vllm_config.model_name_or_path.split("/")[1].replace(".", "_")
    results_dir = f"results/{model_str}/{args.syn_gen_method}"
    os.makedirs(results_dir, exist_ok=True)

    # Run LLM on original benchmark (or load precomputed results)
    orig_fp = fps_df["orig_abs_path"].iloc[0]
    orig_res_fp = f"{results_dir}/orig_results.csv"

    if args.load_orig:
        print(f"\nLoading precomputed original benchmark results from {args.load_orig}")
        orig_res_df = pd.read_csv(args.load_orig)
        orig_res_df.to_csv(orig_res_fp, index=False)
    else:
        print(f"\nEvaluating LLM on original benchmark: {orig_fp}")
        orig_df = pd.read_csv(orig_fp)
        format_data(orig_df).to_csv(f"{results_dir}/orig_formatted.csv", index=False)
        orig_res_df = run_eval(orig_df, llm, sampling_params)
        orig_res_df.to_csv(orig_res_fp, index=False)

    print(f"Accuracy on original benchmark: {orig_res_df['correct'].mean():.3f}")

    # Run LLM on synthetic benchmarks
    for syn_fp in fps_df["syn_abs_path"]:
        syn_df = pd.read_csv(syn_fp)
        syn_name = syn_df["id"].iloc[0].rsplit("_", 1)[0]
        print(f"\nEvaluating LLM on synthetic benchmark: {syn_name} ({syn_fp})")

        syn_fmt_fp = f"{results_dir}/syn_{syn_name}_formatted.csv"
        syn_fmt_df = format_data(syn_df)
        syn_fmt_df.to_csv(syn_fmt_fp, index=False)

        syn_res_fp = f"{results_dir}/syn_results_{syn_name}.csv"
        syn_res_df = run_eval(syn_df, llm, sampling_params)
        syn_res_df.to_csv(syn_res_fp, index=False)
        print(f"Accuracy on synthetic benchmark: {syn_res_df['correct'].mean():.3f}")
