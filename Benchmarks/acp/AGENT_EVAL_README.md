For downstream evaluation on three models, run these one after the other:
1. CUDA_VISIBLE_DEVICES=8,9 bash run_acp.sh vllm_configs/gemma3_1b_it.yaml 2
2. CUDA_VISIBLE_DEVICES=8,9 bash run_acp.sh vllm_configs/llama3_1_8b_it.yaml 2
3. CUDA_VISIBLE_DEVICES=8,9 bash run_acp.sh vllm_configs/qwen3_4b_it.yaml 2