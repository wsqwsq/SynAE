# Benchmarks

Per-benchmark runtimes for the three real-data benchmarks SynAE is built around — **T1-attraction**, **BFCL v4 multi-turn**, and **ACPBench**. Each subdirectory plays two roles in the SynAE pipeline:

1. **Source of real data.** The original benchmark trajectories are the reference dataset that the `synthetic data generation/` pipeline (`create_syn.py`) consumes when producing each synthetic variant. The schemas, attribute ontologies, and pre-/post-processing helpers needed to land that real data in the generator's expected format live here.
2. **Downstream agent evaluation.** Each runtime wires the benchmark's native execution stack to both the original and synthetic data, runs a fixed roster of agents on each, and emits the per-sample results that feed SynAE's **Task Difficulty Difference (TDD)** and **Ranking Divergence (RD)** metrics.

For project background and the upstream pipeline, see the [top-level README](../README.md).

---

## Layout

```
Benchmarks/
├── T1 code/                                # T1-attraction runner (HF transformers)
├── berkeley-function-call-leaderboard/     # BFCL fork with AgentEval glue scripts
├── acp/                                    # ACPBench runner (vLLM)
└── experimental/                           # T1-Augmented prep: validity filter,
                                            # invalidate baselines, case study
```

The three benchmark runtimes are independent — each has its own Python environment (`pyproject.toml` / `requirements.txt`) and its own runner scripts. They share a common contract with the upstream stage: each consumes a `orig_syn_abs_filepath.csv` produced by `collect_orig_syn_fps.py` that maps a run ID to absolute paths for the (original, synthetic) datasets.

---

## Roster of agents

The paper evaluates three open-source agents across all benchmarks:

- `meta-llama/Llama-3.1-8B-Instruct`
- `google/gemma-3-1b-it`
- `Qwen/Qwen3-4B-Instruct-2507`

T1 also uses `Mistral-7B-Instruct` as the LLM-as-a-judge for functional equivalence; ACP uses a rule-based validity check (yes/no) and BFCL uses both BFCL's native scorer and an LLM judge.

---

## T1 code/

T1-attraction runner (CSV-driven, multi-turn, tool-calling). Detailed usage in [`T1 code/AGENT_EVAL_README.md`](T1%20code/AGENT_EVAL_README.md).

**Pipeline:**

1. **Generate synthetic tool calls + outputs** — `create_syn.py` only produces synthetic instructions for T1, so this step fills in the `Tool Call` and `Output` columns:
   ```bash
   python orig_syn_e2e.py <orig_syn_abs_fp.csv>
   ```
   Uses `meta-llama/Llama-3.1-8B-Instruct` via `pe.llm.HuggingfaceLLM` and writes per-run `data/<output_id>/{orig,syn}_inferred.csv` plus `_for_eval.csv` versions.

2. **Run each agent on (orig, syn) benchmarks:**
   ```bash
   python run_llm_on_orig_syn_bench_e2e.py hf_llm_configs/llama3_1_8b_it.yaml <orig_syn_abs_fp.csv>
   python run_llm_on_orig_syn_bench_e2e.py hf_llm_configs/gemma3_1b_it.yaml   <orig_syn_abs_fp.csv>
   python run_llm_on_orig_syn_bench_e2e.py hf_llm_configs/qwen3_4b_it.yaml    <orig_syn_abs_fp.csv>
   ```
   `--load_orig` / `--same_orig` skip re-running the original benchmark across hyperparam sweeps.

3. **LLM-as-a-judge for functional equivalence** between real and synthetic outputs:
   ```bash
   python llm_judge_on_orig_syn_results_e2e.py
   ```
   Uses `Mistral-7B-Instruct` (`hf_llm_configs/judge.yaml`).

**Other files:**

- `inference.py` — `generate_plan` / `generate_output` helpers used by the e2e scripts.
- `evaluation.py` — local metrics (kept for parity with the upstream `SynAE_Evaluation/` scripts; the canonical implementations live there).
- `prepare_ori_data.py`, `merge_data.py`, `syn_data2infer.py` — small data-shaping utilities.
- `get_case_study_attempt2_tc_outputs.py` — generates tool calls + outputs for the case-study Attempt-2 dataset (used together with `experimental/combine_attempt2_base_aug.py`).
- `data/`, `evaluation/`, `src/`, `docs/` — upstream T1 assets bundled with the fork.
- `T1-main.zip` — pristine snapshot of the upstream T1 repo.

**Setup:** `cd "T1 code" && uv sync` (or `pip install -e .`).

---

## berkeley-function-call-leaderboard/

A fork of the [Berkeley Function-Call Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html) with AgentEval glue scripts. Detailed usage in [`berkeley-function-call-leaderboard/AGENT_EVAL_README.md`](berkeley-function-call-leaderboard/AGENT_EVAL_README.md).

**Pipeline (per generation method):**

1. **Land synthetic data into BFCL's expected layout:**
   ```bash
   python format_syn_data_to_bfcl.py <orig_syn_abs_fp.csv>
   ```
   Writes synthetic instructions to `bfcl_eval/data/` and tool calls to `bfcl_eval/data/possible_answer/`.

2. **For methods needing LLM-generated tool calls** (fewshot fixed/random, blankfill): copy the dummy tool calls into `bfcl_eval/data/possible_answer/`, then:
   ```bash
   ./run_<method>_create_syn_tc.sh    # generates tool calls via LLaMA-3.1-8B
   ```
   Overwrite the dummy files with the real outputs.

3. **Format for SynAE's CSV schema** (merge instructions + tool calls into `Id, Data, Tool Calls`):
   ```bash
   ./run_<method>_fmt_for_sb.sh       # one per method: oversample, blankfill, fewshot_*, dropmin, invalidate
   ```

4. **Downstream evaluation** — run each agent against every test category:
   ```bash
   ./run_model_on_all_benchmarks.sh meta-llama/Llama-3.1-8B-Instruct
   ./run_model_on_all_benchmarks.sh google/gemma-3-1b-it
   ./run_model_on_all_benchmarks.sh Qwen/Qwen3-4B-Instruct-2507
   ```
   This invokes `bfcl generate` then `bfcl evaluate`. Scores are written to `score/`.

5. **Aggregate and judge:**
   ```bash
   python collect_model_scores.py                        # score/ → CSV (model, test_category, accuracy, …)
   ./run_format_model_all_gen_to_sb.sh                   # format model outputs for the LLM judge
   ./run_llm_judge_model_all_gen.sh                      # llm_judge.py: LLM yes/no on each sample
   ```

**Method hyperparameter sweeps** (each becomes a `test_category`):

| Method | Hyperparameter values |
|---|---|
| Oversample | `frac0`, `frac0_1`, `frac0_3`, `frac0_5`, `frac0_7`, `frac0_9`, `frac1` |
| Fewshot (fixed) | `ex0`, `ex1`, `ex3`, `ex5` |
| Fewshot (random) | `ex0`, `ex1`, `ex3`, `ex5` |
| Blankfill | `prob0_1`, `prob0_3`, `prob0_5`, `prob0_7`, `prob0_9` |
| Dropmin | `{0,1,2,3}secondary_api_frac0_3` |
| Invalidate | `frac0`, `frac0_1`, …, `frac1` |

**Setup:** follow the upstream BFCL install instructions in `berkeley-function-call-leaderboard/README.md`.

---

## acp/

ACPBench (Applicability & Progression) runner using vLLM for GPU inference. Detailed usage in [`acp/AGENT_EVAL_README.md`](acp/AGENT_EVAL_README.md).

The benchmark answers are boolean (yes/no), so validity is checked by a regex match — no LLM judge needed.

**Run all three agents:**

```bash
CUDA_VISIBLE_DEVICES=8,9 bash run_acp.sh vllm_configs/gemma3_1b_it.yaml   2
CUDA_VISIBLE_DEVICES=8,9 bash run_acp.sh vllm_configs/llama3_1_8b_it.yaml 2
CUDA_VISIBLE_DEVICES=8,9 bash run_acp.sh vllm_configs/qwen3_4b_it.yaml    2
```

`run_acp.sh` iterates the six generation methods (`oversample_without_repl`, `blankfilling`, `fewshot_fixed`, `fewshot_random`, `dropmin`, `invalidate`), reusing the original-dataset results across runs via `--load-orig` after the first method.

**Files:**

- `main_vllm.py` — vLLM-backed runner (preferred path on GPU).
- `main.py` — non-vLLM fallback.
- `vllm_configs/*.yaml` — model + sampling config per agent.
- `requirements.txt`, `pyproject.toml`, `uv.lock`, `mise.toml` — environment.

**Setup:** `cd acp && uv sync`. Requires CUDA + vLLM.

---

## experimental/

Helpers for the **T1-Augmented** experiments (paper §5 and case study). Detailed usage in [`experimental/README.md`](experimental/README.md).

T1-Augmented adds LLM-generated outputs to the original T1 instructions/tool calls; the helpers here filter and stress-test that augmented dataset.

| Step | Script | Purpose |
|---|---|---|
| 1. Validity filter | `get_valid_t1_aug.py` | LLM-as-a-judge drops samples with inconsistent outputs → `orig_valid.csv`. |
| 2.1. Invalidate tool calls | `get_t1_invalidate_tc.py` | Synthesizes failure cases with corrupted tool-call params → `syn_invalidate_tc/`. |
| 2.1. Invalidate outputs | `get_t1_invalidate_output.py` | Same idea, but corrupts city/attraction-type in outputs → `syn_invalidate_out/`. |
| 2.2. Case study | `get_t1_case_study.py` | Builds Base + Attempt-1 + Attempt-2 datasets to demo SynAE on a "broken-then-fixed" scenario → `syn_case_study/`. |
| 2.2. (cont.) | `combine_attempt2_base_aug.py` | Merges the Attempt-2 augmented partition (after running `T1 code/get_case_study_attempt2_tc_outputs.py`) back with the Base dataset. |

Includes the source CSVs needed by these steps:

- `orig_inferred.csv` / `orig_inferred_for_eval.csv` — outputs of `T1 code/orig_syn_e2e.py` on the original benchmark.
- `orig_valid.csv` — output of `get_valid_t1_aug.py`.
- `ontology_t1_attraction_data.csv` — the city/attraction-type ontology used for invalidation.

**Setup:** `pip install -r requirements.txt` (or `uv sync`).

---

## Interaction with `synthetic data generation/`

Each benchmark talks to the upstream generator in two directions:

**Upstream (real data → generator).** The benchmark's original trajectories are loaded by the per-benchmark loader under `synthetic data generation/benchmarks/` (e.g. `t1_attraction.py`, `bfcl_multiturn_base.py`, `acp_app_prog.py`) and pre-processed into the generator's uniform schema. Generation methods (`oversample`, `blankfill`, `fewshot*`, `invalidate`, `dropmin`) then operate on that schema and write per-run synthetic CSVs under `outputs/<date>/<time>/` or `multirun/<date>/<time>/<run_idx>/`.

**Downstream (generator → benchmark runtime).** After generation, pair the original/synthetic file paths into one CSV:

```bash
cd "synthetic data generation"
uv run python collect_orig_syn_fps.py --runs_dir outputs/<date>/<time>
```

The resulting CSV (`output_id, orig_abs_path, syn_abs_path`) is the first positional argument to each benchmark's main runner script (`orig_syn_e2e.py`, `format_syn_data_to_bfcl.py`, `run_acp.sh`).
