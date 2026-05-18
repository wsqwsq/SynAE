TEST_CATEGORIES=(
    "invalidate_frac0"
    "invalidate_frac0_1"
    "invalidate_frac0_2"
    "invalidate_frac0_3"
    "invalidate_frac0_4"
    "invalidate_frac0_5"
    "invalidate_frac0_6"
    "invalidate_frac0_7"
    "invalidate_frac0_8"
    "invalidate_frac0_9"
    "invalidate_frac1"
)

for category in "${TEST_CATEGORIES[@]}"; do
  python format_bfcl_to_sb.py bfcl_eval/data/BFCL_v4_$category.json bfcl_eval/data/possible_answer/BFCL_v4_$category.json
done