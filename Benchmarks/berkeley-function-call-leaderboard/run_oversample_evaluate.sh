MODEL=${1:-meta-llama/Llama-3.1-8B-Instruct}

bfcl evaluate --model=$MODEL --test-category=oversample_frac0_1,oversample_frac0_3,oversample_frac0_5,oversample_frac0_7,oversample_frac0_9,oversample_frac0,oversample_frac1 --save-decoded