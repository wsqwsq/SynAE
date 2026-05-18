Steps to generate synthetic T1: 
1. Run structbench_syndata `create_syn.py` with the desired hyperparams, the results will be saved to a directory.
2. Run structbench_syndata `collect_orig_syn_fps.py`, pass the results dirpath from the previous step. This will save a CSV file with the orig and syn data filepaths to a CSV file.
3. Run `orig_syn_e2e.py`, pass the filepaths CSV from the previous step. This generates the synthetic tool calls and outputs columns, since structbench_syndata can only generate the instructions.

Steps to run downstream evaluation on T1:
1. Run `run_llm_on_orig_syn_bench_e2e.py` on three models: meta-llama/Llama-3.1-8B-Instruct, google/gemma-3-1b-it, Qwen/Qwen3-4B-Instruct-2507. This will create the LLM "answers" to each (original, synthetic) benchmark. 
2. Run `llm_judge_on_orig_syn_results_e2e.py` for all the results from the previous step. 