import argparse
import os
import pandas as pd
import yaml
from pe.llm import HuggingfaceLLM
from inference import generate_plan
from orig_syn_e2e import format_data_for_eval
from dataclasses import dataclass
from transformers import AutoTokenizer


@dataclass
class HfLlmConfig:
    model_name_or_path: str
    max_completion_tokens: int
    batch_size: int
    temperature: float


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to generate LLM's benchmark results on orig_inferred and syn_inferred")
    parser.add_argument(
        "hf_llm_config",
        type=str,
        help="Path to YAML file with HuggingfaceLLM params"
    )
    parser.add_argument(
        "orig_syn_abs_fp_filepath",
        type=str,
        help="Path to file with output ID and absolute filepaths for original and synthetic data"
    )
    parser.add_argument(
        "--load_orig",
        type=str,
        help="Path to precomputed orig_inferred.csv. If provided, loads instead of computing. "
             "Useful for hyperparameter sweeps that use the same orig dataset."
    )
    parser.add_argument(
        "--same_orig",
        action="store_true",
        help="Run inference on orig dataset only once. Useful for hyperparam sweeps that use the same orig dataset.")
    args = parser.parse_args()

    # Setup LLM under test
    llm_config_fp = args.hf_llm_config
    with open(llm_config_fp) as stream:
        try:
            hf_llm_config = HfLlmConfig(**yaml.safe_load(stream))
            print(f"Testing LLM with {hf_llm_config=} on both orig and syn benchmark data...")
        except yaml.YAMLError as exc:
            print(exc)

    tokenizer = AutoTokenizer.from_pretrained(hf_llm_config.model_name_or_path)
    llm = HuggingfaceLLM(
        model_name_or_path=hf_llm_config.model_name_or_path,
        max_completion_tokens=hf_llm_config.max_completion_tokens,
        batch_size=hf_llm_config.batch_size,
        temperature=hf_llm_config.temperature,
        tokenizer=tokenizer
    )
    model_name = hf_llm_config.model_name_or_path.split("/")[1]

    fps_df = pd.read_csv(args.orig_syn_abs_fp_filepath)
    if args.load_orig and args.same_orig:
        print(
            "Warning: Both --load_orig and --same_orig provided. Using --load_orig (--same_orig ignored).")
    elif args.load_orig:
        print(
            "--load_orig provided. Orig LLM results dataset will be loaded from filepath.")
    elif args.same_orig:
        print(
            "--same_orig provided. LLM result generation on the orig dataset will only run once.")
    else:
        print("LLM result generation on the orig dataset will run each time.")

    orig_llm_df = None
    if args.load_orig:
        print(f"Loading original LLM results data from {args.load_orig}...")
        orig_llm_df = pd.read_csv(args.load_orig)

    for row in fps_df.itertuples(index=False):
        output_id = row.output_id

        print(f"Starting run for {output_id=}...")
        output_dir = f"data/{output_id}"

        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        orig_abs_path = f"{output_dir}/orig_inferred.csv"
        syn_abs_path = f"{output_dir}/syn_inferred.csv"

        if orig_llm_df is not None and (args.load_orig or args.same_orig):
            print("Reusing orig df...")
        else:
            print(f"Generating results on original data for {model_name}...")
            orig_df = pd.read_csv(orig_abs_path)
            orig_llm_df = generate_plan(data=orig_df, llm=llm)

        orig_out_fp = f"{output_dir}/orig_{model_name}.csv"
        orig_llm_df.to_csv(orig_out_fp, index=False)
        print(f"Saved data to {orig_out_fp}")

        print("Formatting original LLM results data for evaluation...")
        orig_for_eval_df = format_data_for_eval(df=orig_llm_df)

        orig_eval_out_fp = f"{output_dir}/orig_{model_name}_for_eval.csv"
        orig_for_eval_df.to_csv(orig_eval_out_fp, index=False)
        print(f"Saved data to {orig_eval_out_fp}")

        print(f"Generating results on synthetic data for {model_name}...")
        syn_df = pd.read_csv(syn_abs_path)
        syn_llm_df = generate_plan(data=syn_df, llm=llm)

        syn_out_fp = f"{output_dir}/syn_{model_name}.csv"
        syn_llm_df.to_csv(syn_out_fp, index=False)
        print(f"Saved data to {syn_out_fp}")

        print("Formatting synthetic LLM results data for evaluation...")
        syn_for_eval_df = format_data_for_eval(df=syn_llm_df)

        syn_eval_out_fp = f"{output_dir}/syn_{model_name}_for_eval.csv"
        syn_for_eval_df.to_csv(syn_eval_out_fp, index=False)
        print(f"Saved data to {syn_eval_out_fp}")
