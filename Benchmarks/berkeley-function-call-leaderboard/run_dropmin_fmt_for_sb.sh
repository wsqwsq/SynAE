TEST_CATEGORIES=(
  "dropmin_0secondary_api_frac0_3"
  "dropmin_1secondary_api_frac0_3"
  "dropmin_2secondary_api_frac0_3"
  "dropmin_3secondary_api_frac0_3"
)

for category in "${TEST_CATEGORIES[@]}"; do
  python format_bfcl_to_sb.py bfcl_eval/data/BFCL_v4_$category.json bfcl_eval/data/possible_answer/BFCL_v4_$category.json
done