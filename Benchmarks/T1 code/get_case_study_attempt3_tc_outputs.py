import pandas as pd
from pathlib import Path
from pe.llm import HuggingfaceLLM
from inference import generate_plan
from orig_syn_e2e import format_data_for_eval

OUTPUT_DIR = "../experimental/syn_case_study"

llm = HuggingfaceLLM(
    max_completion_tokens=100,
    batch_size=8,
    model_name_or_path="meta-llama/Llama-3.1-8B-Instruct",
    temperature=0.5
)

nemo_aug_paths = [
    f"{OUTPUT_DIR}/attempt3_nemotron_aug.csv",
    f"{OUTPUT_DIR}/attempt3_llama_aug.csv",
    f"{OUTPUT_DIR}/attempt3_gpt4omini_aug.csv",
]

for fp in nemo_aug_paths:
    print(f"Generating plan and output for attempt3_aug syn data ({fp})...")
    aug_df = pd.read_csv(fp)

    # Convert to T1-compatible format i.e. split sample over multiple lines
    aug_ids_list = []
    aug_conv_lines_list = []
    for i, aug_conv in enumerate(aug_df["Data"]):
        aug_conv_lines = aug_conv.split("\n")
        aug_ids_list.extend([i] * len(aug_conv_lines))
        aug_conv_lines_list.extend(aug_conv_lines)
    aug_t1_df = pd.DataFrame({"ID": aug_ids_list, "Filled_Template": aug_conv_lines_list})

    # Generate instructions and tool calls
    aug_inferred_df = generate_plan(data=aug_t1_df, llm=llm)

    # Format dataset
    aug_inferred_df = format_data_for_eval(df=aug_inferred_df)

    # Save dataset to the case study directory
    fname = Path(fp).stem
    aug_output_fp = f"{OUTPUT_DIR}/{fname}_inferred.csv"
    aug_inferred_df.to_csv(aug_output_fp, index=False)
    print(f"Saved attempt3_aug with inferred tool calls and outputs to {aug_output_fp}!")
