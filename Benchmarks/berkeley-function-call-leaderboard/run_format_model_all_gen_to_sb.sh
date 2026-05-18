MODEL=${1:-google/gemma-3-1b-it}

TEST_CATEGORIES=(
    "multi_turn_base"
    "oversample_frac0_1"
    "oversample_frac0_3"
    "oversample_frac0_5"
    "oversample_frac0_7"
    "oversample_frac0_9"
    "oversample_frac0"
    "oversample_frac1"
    "fewshot_fixed_ex0"
    "fewshot_fixed_ex1"
    "fewshot_fixed_ex3"
    "fewshot_fixed_ex5"
    "fewshot_rand_ex0"
    "fewshot_rand_ex1"
    "fewshot_rand_ex3"
    "fewshot_rand_ex5"
    "blankfill_prob0_1"
    "blankfill_prob0_3"
    "blankfill_prob0_5"
    "blankfill_prob0_7"
    "blankfill_prob0_9"
    "dropmin_0secondary_api_frac0_3"
    "dropmin_1secondary_api_frac0_3"
    "dropmin_2secondary_api_frac0_3"
    "dropmin_3secondary_api_frac0_3"
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
    python format_model_gen_to_sb.py --model=$MODEL --test-category=$category
done
