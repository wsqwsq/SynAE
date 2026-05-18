TEST_CATEGORIES=(
  "oversample_frac0_1"
  "oversample_frac0_3"
  "oversample_frac0_5"
  "oversample_frac0_7"
  "oversample_frac0_9"
  "oversample_frac0"
  "oversample_frac1"
)

for category in "${TEST_CATEGORIES[@]}"; do
  python format_bfcl_to_sb.py bfcl_eval/data/BFCL_v4_$category.json bfcl_eval/data/possible_answer/BFCL_v4_$category.json
done