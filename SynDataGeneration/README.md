# structbench-syndata

A tool for generating synthetic data from original benchmark datasets.

## Setup

Install dependencies using uv:

```bash
uv sync
```

This will install all required packages (including Hydra for experiment management).

## Using create_syn.py

The `create_syn.py` script is a Hydra-managed experiment runner that generates synthetic data from original datasets. 
Configuration is managed through YAML files in the `configs_syn` directory.

### Basic Usage

Run with default configuration:

```bash
uv run python create_syn.py
```

This uses the default config in configs_syn/config.yaml, which loads:
- `orig_data`: t1_attraction configuration
- `syn_data`: oversample generation method

### Configuration Structure

Configuration files are organized hierarchically:

- `configs_syn/config.yaml`: Main config file with defaults
- `configs_syn/orig_data/`: Original data configurations (benchmark type, file paths)
- `configs_syn/syn_data/`: Synthetic data generation method configurations

### Overriding Configuration

Override specific parameters using Hydra syntax:

```bash
# Use a different original data config
uv run python create_syn.py orig_data=t1_attraction_full

# Override generation parameters
uv run python create_syn.py syn_data.gen_params.dup_frac=0.7

# Override multiple parameters
uv run python create_syn.py syn_data.gen_params.seed=456 syn_data.gen_params.dup_frac=0.6
```

### Multirun

Run with multiple different configurations using Hydra syntax: 

```bash
# Sweep over different dup_frac values for the oversample generation method
python create_syn.py -m orig_data=t1_attraction syn_data=oversample syn_data.gen_params.dup_frac=0.1,0.2
```

### Output

Results for a run are saved to an `output_dir` with:
- `orig_df.csv`: Loaded original data
- `orig_df_proc.csv`: Pre-processed original data
- `syn_df_proc.csv`: Generated synthetic data (processed)
- `syn_df.csv`: Final synthetic data (post-processed)
- `.hydra/`: Hydra configuration snapshots

For single runs, the `output_dir` is `outputs/YYYY-MM-DD/HH-MM-SS/`.

For multiruns, the `output_dir` is `multirun/YYYY-MM-DD/HH-MM-SS/run_idx`.

### Benchmarks

Currently supported: 
- `t1_attraction`: Uses `t1_attraction` train split 1 as the original data.
- `t1_attraction_med`: Uses `t1_attraction` train splits 1-15 as the original data.
- `t1_attraction_full`: Uses `t1_attraction` train split 1-25 as the original data.

### Generation Methods

Currently supported:
- `oversample`: Duplicates specified samples to reach a target fraction of the dataset.
- `blankfill`: Masks each sample randomly and uses an LLM to fill in the blanks.
- `fewshot`: Passes a few samples to the LLM, which then has to generate similar samples.

### Utilities

`extract_time.py`: 
1. Collects the time taken to generate synthetic data for each run in the specified directory. 
2. Supports reading single and multirun directories.

`collect_orig_syn_fps.py`: 
1. Collects the absolute original and synthetic dataset filepaths for each run in the specified directory. 
2. Supports reading single and multirun directories. 