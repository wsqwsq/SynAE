# SynAE_Evaluation

Metric implementations for **SynAE**, the multi-axis evaluation framework that scores synthetic agent benchmarks against a real reference dataset. Each script in this directory takes a synthetic CSV produced by the `synthetic data generation/` pipeline (and the corresponding original data) and writes a JSON of metrics covering **fidelity**, **diversity**, and (where applicable) **validity** across instructions, tool calls, and outputs.

For project background and the high-level pipeline, see the [top-level README](../README.md).

---

## Layout

```
SynAE_Evaluation/
├── evaluation_T1.py        # Metrics for the T1-attraction benchmark
├── evaluation_bfcl.py      # Metrics for BFCL v4 multi-turn
├── evaluation_acp.py       # Metrics for ACPBench (Applicability & Progression)
└── precision_recall.py     # Shared KNN-Precision/Recall + FID utilities
```

The three benchmark scripts share the same overall structure (a `FUNC_LIST` of metric functions invoked by `evaluate_all`) but differ in:

- The schema of the input CSV they expect.
- Which tools / attributes are tracked.
- Which CFG / structural metrics apply.

---

## Input format

All three scripts expect a synthetic CSV with at least a `Data` column (the conversation transcript). Other columns vary by benchmark:

| Script | Expected columns |
|---|---|
| `evaluation_T1.py` | `Data`, `Tool Call`, `Output`, plus attributes `city`, `type` |
| `evaluation_bfcl.py` | `Data`, `Tool Calls`, plus `primary_api`, `secondary_api`, `conv_len` |
| `evaluation_acp.py` | `Data`, `Output`, plus `primary_api`, `secondary_api`, `conv_len` |

A separate **attribute-category CSV** lists the universe of values each categorical attribute can take (used for TV-distance and entropy computations).

The original / reference dataset is loaded from a fixed path inside each script (e.g. `../ori_data/orig_inferred_for_eval.csv` for T1) — adjust `priv_data_path` near the top of the script if your data lives elsewhere.

---

## Running

Each script exposes the same CLI:

```bash
python evaluation_T1.py \
    --syn_data_path      ../syn_data/oversample_05/syn_inferred_for_eval.csv \
    --save_path          ../eval_results/oversample_05.json \
    --attr_category_path ../ori_data/category.csv \
    --method_name        oversample_r0.5
```

| Flag | Purpose |
|---|---|
| `--syn_data_path` | Path to the synthetic CSV produced by the generation pipeline. |
| `--save_path` | Output JSON. If the file exists, the new entry is appended/overwritten under the `--method_name` key. |
| `--attr_category_path` | CSV listing the value universe for each categorical attribute. |
| `--method_name` | Label under which results are stored in the output JSON. |

The bottom of each script also contains a hardcoded sweep loop (e.g. across `oversample_*`, `blankfill_*`, `fewshot_*`) — useful as a template for batch runs but currently commented in/out manually.

Embeddings of the **reference** data are cached in process-level dicts (`cached_embedding`) so repeated metric calls within a single run reuse them. Run-to-run caching is not done, so prefer running a full sweep in a single invocation.

---

## Metric reference

`evaluate_all` runs every function in `FUNC_LIST` and collects the returned dicts into one results object. The shared metric set (T1 / BFCL / ACP):

| Function | Pillar | What it measures |
|---|---|---|
| `evaluate_length` | Fidelity | Wasserstein distance between total / per-speaker token-length distributions |
| `evaluate_round` | Fidelity | Wasserstein distance on number of conversation rounds (T1, BFCL) |
| `evaluate_precision_recall` | Fidelity | KNN-Precision/Recall on sentence-transformer embeddings of full transcripts |
| `evaluate_fid` | Fidelity | Fréchet distance on the same embeddings |
| `evaluate_pair_similarity` | Fidelity | Cosine similarity of consecutive (assistant→user, user→assistant) turn embeddings (T1) |
| `evaluate_attr` | Fidelity | TV distance between original/synthetic categorical-attribute distributions |
| `evaluate_tool_calling` | Fidelity | Tool-call length distance + 1/2/3-step planning TV distance over tool sequences |
| `evaluate_output` | Fidelity | Output token-length Wasserstein + KNN-P/R on output embeddings (T1, ACP) |
| `evaluate_attr_entropy` | Diversity | Shannon entropy of joint attribute distribution in the synthetic set |
| `evaluate_vendi` | Diversity | Vendi score on synthetic embeddings |
| `evaluate_CFG` / `evaluate_TTR` | Validity / Diversity | Fraction of CFG-valid samples (parsed via Lark grammar) and type-token ratio (defined; toggle by adding to `FUNC_LIST`) |

See `precision_recall.py` for the KNN-P/R and FID implementations (adapted from [`improved-precision-and-recall-metric`](https://github.com/kynkaat/improved-precision-and-recall-metric)).

The metric set can be edited per-run by adjusting `FUNC_LIST` near the bottom of each script.

---

## Output format

`save_or_update_results_json` writes a JSON keyed by `--method_name`:

```json
{
  "oversample_r0.5": {
    "Method": "oversample_r0.5",
    "Task: total token length": 0.083,
    "Task: precision": 0.91,
    "Task: recall": 0.88,
    "Task: FID": 1.24,
    "Tool Calling: 1-step TV distance": 0.06,
    "Output: precision": 0.93,
    "Diversity: attribute entropy": 2.71,
    "Diversity: Vendi": 142.3
  },
  "blankfill_p0.3": { ... }
}
```

Re-running a method with the same `--save_path` and `--method_name` overwrites that entry only — other entries are preserved. This makes it safe to extend an existing results file across many methods.

---

## Dependencies

```
numpy pandas scipy scikit-learn faiss-cpu torch
sentence-transformers vendi-score python-Levenshtein
lark matplotlib seaborn tqdm
```

`precision_recall.py` lives alongside the evaluation scripts and is imported directly — no install needed.
