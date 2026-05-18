#!/bin/bash

VLLM_CONFIG=${1:?"Usage: $0 <vllm_config> [--num-gpus N]"}
NUM_GPUS=${2:-2}

SYNDATA_BASE="../../structbench_syndata"

ACP_METHODS=(
  "oversample_without_repl"
  "blankfilling"
  "fewshot_fixed"
  "fewshot_random"
  "dropmin"
  "invalidate"
)

ACP_DIRS=(
  "multirun/2026-02-19/12-09-10"
  "multirun/2026-02-19/12-51-16"
  "multirun/2026-02-19/12-37-33"
  "multirun/2026-02-19/12-23-27"
  "multirun/2026-02-19/12-10-33"
  "multirun/2026-02-19/12-15-36"
)

MODEL_STR=$(python -c "import yaml; c=yaml.safe_load(open('${VLLM_CONFIG}')); print(c['model_name_or_path'].split('/')[-1].replace('.','_'))")

for i in "${!ACP_METHODS[@]}"; do
  method="${ACP_METHODS[$i]}"
  fp="${SYNDATA_BASE}/${ACP_DIRS[$i]}/orig_syn_abs_filepath.csv"
  echo "=== Running ACP eval: ${method} ==="
  if [ "$i" -eq 0 ]; then
    python main_vllm.py "${VLLM_CONFIG}" "${fp}" "${method}" --num-gpus "${NUM_GPUS}"
    ORIG_RESULTS="results/${MODEL_STR}/${ACP_METHODS[0]}/orig_results.csv"
  else
    python main_vllm.py "${VLLM_CONFIG}" "${fp}" "${method}" --num-gpus "${NUM_GPUS}" --load-orig "${ORIG_RESULTS}"
  fi
done
