import argparse
from dataclasses import dataclass

import pandas as pd
import yaml
from inspect_ai import Task, task
from inspect_ai import eval_set
from inspect_ai.dataset import Sample, csv_dataset
from inspect_ai.model import get_model
from inspect_ai.scorer import match, pattern
from inspect_ai.solver import generate, prompt_template


@dataclass
class VllmConfig:
    model_name_or_path: str
    max_completion_tokens: int
    temperature: float


# Source: https://github.com/IBM/ACPBench/blob/main/evals/acpbench.py
BOOLEAN_TEMPLATE = """{context}
{prompt}
Only answer yes or no."""

# Source: https://github.com/IBM/ACPBench/blob/main/evals/acpbench.py
BOOLEAN_REGEX = r"((?<=The answer is )(.*)(?=.)|(?<=the answer is )(.*)(?=.)|(?<=The answer: )(.*)(?=.)|(?<=The final answer: )(.*)(?=.)|(?<=..Final Answer..: )(.*)(?=.)|(?<=..answer..: )(.*)(?=.)|(?<=..Answer..: )(.*)(?=.)|\b(Yes|No|yes|no)\b)"


# Modified version of source: https://github.com/IBM/ACPBench/blob/main/evals/acpbench.py
def record_to_sample(record):
    """Convert ACP CSV dataset record to Inspect Sample"""
    return Sample(
        input=record.get("question", ""),
        target=record.get("answer", ""),
        metadata={
            "context": record.get("context", ""),
            "group": record.get("group", ""),
        },
    )


def load_acp_dataset(dataset_path: str):
    return csv_dataset(dataset_path, record_to_sample)


@task
def create_task(dataset_path: str):
    return Task(
        dataset=load_acp_dataset(dataset_path),
        solver=[prompt_template(BOOLEAN_TEMPLATE), generate()],
        scorer=pattern(pattern=BOOLEAN_REGEX),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script to run ACP benchmarks on LLMs")
    parser.add_argument(
        "vllm_config", type=str, help="Path to YAML file with vllm LLM params"
    )
    parser.add_argument(
        "orig_syn_abs_fp_filepath",
        type=str,
        help="Path to file with output ID and absolute filepaths for original and synthetic data",
    )
    parser.add_argument("syn_gen_method", type=str, help="Name of syn gen method")
    args = parser.parse_args()

    # Setup LLM under test
    llm_config_fp = args.vllm_config
    with open(llm_config_fp) as stream:
        try:
            vllm_config = VllmConfig(**yaml.safe_load(stream))
            print(
                f"Testing LLM with {vllm_config=} on both orig and syn benchmark data..."
            )
        except yaml.YAMLError as exc:
            print(exc)
    model = get_model(
        model=f"vllm/{vllm_config.model_name_or_path}",
        max_tokens=vllm_config.max_completion_tokens,
        temperature=vllm_config.temperature,
    )

    # Setup eval set with orig and syn benchmarks for the syn gen method
    fps_df = pd.read_csv(args.orig_syn_abs_fp_filepath)

    tasks = []
    orig_fp = fps_df["orig_abs_path"].iloc[0]
    orig_task = create_task(dataset_path=orig_fp)
    tasks.append(orig_task)
    for syn_fp in fps_df["syn_abs_path"]:
        syn_task = create_task(dataset_path=syn_fp)
        tasks.append(syn_task)

    eval_set(tasks, model, log_dir=f"logs_{args.syn_gen_method}")
