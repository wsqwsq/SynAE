TEST_CATEGORIES=(
  "fewshot_rand_ex0"
  "fewshot_rand_ex1"
  "fewshot_rand_ex3"
  "fewshot_rand_ex5"
)

for category in "${TEST_CATEGORIES[@]}"; do
  python format_bfcl_to_sb.py bfcl_eval/data/BFCL_v4_${category}.json score/meta-llama_Llama-3.1-8B-Instruct/multi_turn/BFCL_v4_${category}_score_tool_calls_syn_tc.json
done