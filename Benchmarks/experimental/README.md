# T1-Augmented Experiments

T1-Augmented data was constructed for the paper because the original T1 benchmark data only had instructions and tool calls. 

So we created outputs for each original benchmark sample using an LLM. This process does not guarantee that the outputs generated are correct. 
Using T1-Augmented without any post-processing is problematic for our validity results, because even the original benchmark won't have a perfect validity score. 

So, the pre-requisite for the validity experiments and the case study, is to perform Step 1 below.

## Step 1. Get Valid T1-Augmented Data

Before running the validity experiments on the T1-Augmented data, we need to filter out invalid samples. 
This means we'll use an LLM-as-a-judge on each original sample, and drop the ones that the judge says are invalid.

The judge takes: 
1. Instructions
2. Tool Calls
3. LLM-generated Outputs

The judge returns yes or no, depending on whether the LLM-generated Outputs look consistent to the Instructions and Tool Calls.

Of course, because the judge is also an LLM, there's a chance that we'll have false positives and false negatives.
For now, we'll assume the judge is an ideal classifier. 

Run get_valid_t1_aug.py to get T1-Augmented-Valid (saved to orig_valid.csv). 
This dataset will only contain samples that were judged to be valid. 

Steps 2.1. and 2.2. can then be worked on in parallel.

## Step 2.1. Invalidate Syn Gen

Starting from orig_valid.csv, we'll invalidate the Tool Calls and Outputs for k = 0, 0.1, 0.2, ... 1 samples.
This is an artificial synthetic benchmark creation method so we can verify SynAE's validity metrics actually capture valid/invalid samples.

### Invalidate Tool Calls

Similar to BFCL, we can invalidate Tool Calls by introducing wrong parameter values in each tool call.

Run get_t1_invalidate_tc.py to generate and save the synthetic benchmarks (saved to syn_invalidate_tc/).

### Invalidate Outputs

We can invalidate outputs by replacing the city and/or attraction types. 

Run get_t1_invalidate_output.py to generate and save the synthetic benchmarks (saved to syn_invalidate_out/).

## Step 2.2. Case Study

We create artificial bad datasets so that a developer can see how to use SynAE. 

The ideal dataset will be T1-Augmented-Valid. Starting from here, we'll introduce "mistakes":
1. Base dataset: Dropmin to drop a fraction of attraction_type samples 
2. Attempt 1: Duplicating existing samples, and re-labelling the Instructions attraction_type to inflate the dataset
3. Attempt 2: Fewshot generation to generate samples for the dropped attraction_type
4. Attempt 3: NeMo Data Designer generation to generate samples for the dropped attraction_type

Run get_t1_case_study.py to get the three datasets (saved to syn_case_study/).

### Attempt 2: Fewshot generation

Note: For generating Attempt 2 data, there are two more steps after running get_t1_case_study.py. 

1. Run T1 code's get_case_study_attempt2_tc_outputs.py to get the tool calls and outputs for the augmented part of the data.
2. Run combine_attempt2_base_aug.py to combine the Base dataset with the augmented (now with tool calls and outputs) dataset.

### Attempt 3: NeMo Data Designer Generation

Deploy the NeMo Data Designer following https://docs.nvidia.com/nemo/microservices/25.12.0/design-synthetic-data-from-scratch-or-seeds/docker-compose.html. 

1. Copy base.csv and orig_valid.csv into your data designer scripts directory. Copy the scripts in SynDataGeneration/experimental/t1_nemo to this directory.
2. Run t1_gen_dropped_classes.py from within this directory:
   ```
   python t1_gen_dropped_classes.py
   ```
   The script computes n_to_add per dropped type as the count difference between orig_valid and base, then generates that many samples using NeMo. Outputs (syn_df_proc.csv and syn_df.csv) are saved to the Hydra run directory. 
3. Rename the "Filled_Template" column in syn_df_proc.csv to "Data".
4. Run T1 code's get_case_study_attempt3_tc_outputs.py on the generated syn_df.csv to get tool calls and outputs.
5. Run combine_attempt3_base_aug.py to combine the Base dataset with the augmented dataset. Since this is run once per model, pass the paths explicitly:
   ```
   python combine_attempt3_base_aug.py --aug-inferred <path_to_inferred_aug.csv> --output syn_case_study/attempt3_<model_name>.csv
   ```

### Attempt 4: APIGen-MT generation

Uses [APIGen-MT](https://arxiv.org/pdf/2504.03601): a verified task blueprint (instruction, groundtruth tool calls, expected output) is generated and validated first, then a simulated human-agent conversation is collected against that blueprint.

- No separate policy-rule checker (T1's attraction domain has no τ-bench-style policy engine, so those constraints are folded into the generator's prompt instead).
- No Reverse Task Recombination (Attempts 1-3 all target single-topic ~6-turn conversations, so complex multi-step task composition is skipped).
- Only the first successful trajectory per blueprint is kept (Section 3.2.2 keeps the union of all successful trials across up to 3 attempts); Attempt 4 targets an exact per-type sample quota matching Attempts 1-3, so extra successes would overshoot it.
- The state-based trajectory check (Figure 9's `diff_patch`, "similar to `git diff`") is a DB-mutation concept from τ-bench's write APIs; T1's attraction tools are read-only, so `cache_matches_diff_patch` approximates it with a value-containment check rather than a literal state diff.

Note: For generating Attempt 4 data, there are two more steps after running get_t1_case_study.py.

1. Run T1 code's get_case_study_attempt4_blueprints.py to generate and validate task blueprints for the dropped attraction types (saved to syn_case_study/attempt4_blueprints.csv).
2. Run T1 code's get_case_study_attempt4_tc_outputs.py to simulate human-agent trajectories against those blueprints (saved to syn_case_study/attempt4_aug_inferred.csv).
3. Run combine_attempt4_base_aug.py to combine the Base dataset with the augmented dataset.

All parameters are set in T1 code's apigen_mt_config.py (APIGenMTConfig). Pass `--config path/to/config.yaml` to override defaults, or `--backend openai` to switch from the default local vLLM backend to a hosted OpenAI model.
