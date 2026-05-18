MODEL=${1:-meta-llama/Llama-3.1-8B-Instruct}

CUDA_VISIBLE_DEVICES=6,7 bfcl generate --model=$MODEL --test-category=oversample_frac0_1,oversample_frac0_3,oversample_frac0_5,oversample_frac0_7,oversample_frac0_9,oversample_frac0,oversample_frac1 --backend=vllm --num-gpus=2