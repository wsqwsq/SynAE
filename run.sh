#!/usr/bin/env bash
# Minimal end-to-end SynAE pipeline: generate synthetic data, then evaluate.
# Usage: ./run.sh [benchmark] [method] [param]
#   benchmark: t1 | bfcl | acp        (default: t1)
#   method:    oversample | blankfill | fewshot | invalidate   (default: oversample)
#   param:     numeric hyperparameter for the method           (default: 0.5)

set -euo pipefail

BENCH="${1:-t1}"
METHOD="${2:-oversample}"
PARAM="${3:-0.5}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GEN_DIR="$ROOT/SynDataGeneration"
EVAL_DIR="$ROOT/SynAE_Evaluation"

case "$BENCH" in
    t1)   ORIG_CFG="t1_attraction"; EVAL_SCRIPT="evaluation_T1.py" ;;
    bfcl) ORIG_CFG="bfcl_multiturn_base"; EVAL_SCRIPT="evaluation_bfcl.py" ;;
    acp)  ORIG_CFG="acp_app_prog"; EVAL_SCRIPT="evaluation_acp.py" ;;
    *) echo "Unknown benchmark: $BENCH"; exit 1 ;;
esac

case "$METHOD" in
    oversample) PARAM_KEY="syn_data.gen_params.dup_frac" ;;
    blankfill)  PARAM_KEY="syn_data.gen_params.blank_probability" ;;
    fewshot)    PARAM_KEY="syn_data.gen_params.n_examples" ;;
    invalidate) PARAM_KEY="syn_data.gen_params.invalidate_frac" ;;
    *) echo "Unknown method: $METHOD"; exit 1 ;;
esac

echo "=== [1/2] Generating synthetic data: $BENCH / $METHOD=$PARAM ==="
cd "$GEN_DIR"
uv run python create_syn.py \
    orig_data="$ORIG_CFG" \
    syn_data="$METHOD" \
    "$PARAM_KEY=$PARAM"

LATEST_RUN="$(ls -td outputs/*/* | head -1)"
SYN_CSV="$LATEST_RUN/syn_df.csv"
echo "Synthetic data: $SYN_CSV"

echo "=== [2/2] Running SynAE evaluation ==="
cd "$EVAL_DIR"
mkdir -p ../eval_results
python "$EVAL_SCRIPT" \
    --syn_data_path  "$GEN_DIR/$SYN_CSV" \
    --save_path      "$ROOT/eval_results/${BENCH}_${METHOD}_${PARAM}.json" \
    --method_name    "${METHOD}_${PARAM}"

echo "Done. Results: $ROOT/eval_results/${BENCH}_${METHOD}_${PARAM}.json"
