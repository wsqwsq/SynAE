MODEL=${1:-meta-llama/Llama-3.1-8B-Instruct}
MODEL_DIR=${2:-meta-llama_Llama-3.1-8B-Instruct}

TEST_CATEGORIES=(
  "fewshot_rand_ex0"
  "fewshot_rand_ex1"
  "fewshot_rand_ex3"
  "fewshot_rand_ex5"
)
TEST_CATEGORIES_STR=$(IFS=,; echo "${TEST_CATEGORIES[*]}")

CUDA_VISIBLE_DEVICES=8,9 bfcl generate --model=${MODEL} --test-category=${TEST_CATEGORIES_STR} --backend=vllm --num-gpus=2
bfcl evaluate --model=${MODEL} --test-category=${TEST_CATEGORIES_STR} --save-decoded

for category in "${TEST_CATEGORIES[@]}"; do
  python bfcl_eval/scripts/extract_ground_truth_tool_calls.py score/${MODEL_DIR}/multi_turn/BFCL_v4_${category}_score.json syn_tc
done