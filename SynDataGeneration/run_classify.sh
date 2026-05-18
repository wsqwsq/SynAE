T1_SYN_RESULT_DIRS=(
  "multirun/2026-01-28/14-21-30" # oversample without replacement
  "multirun/2026-01-26/22-41-42" # blankfilling
  "multirun/2026-01-26/22-59-12" # fewshot fixed
  "multirun/2026-01-28/16-29-08" # fewshot random
  "multirun/2026-02-15/23-11-52" # dropmin
)

BFCL_SYN_RESULT_DIRS=(
  "multirun/2026-02-02/21-51-37" # oversample without replacement
  "multirun/2026-02-04/22-10-50" # blankfilling
  "multirun/2026-02-04/00-30-54" # fewshot fixed
  "multirun/2026-02-04/00-31-19" # fewshot random
  "multirun/2026-02-15/23-12-28" # dropmin
  "multirun/2026-02-19/12-17-26" # invalidate
)

ACP_SYN_RESULT_DIRS=(
  "multirun/2026-02-19/12-09-10" # oversample without replacement
  "multirun/2026-02-19/12-51-16" # blankfilling
  "multirun/2026-02-19/12-37-33" # fewshot fixed
  "multirun/2026-02-19/12-23-27" # fewshot random
  "multirun/2026-02-19/12-10-33" # dropmin
  "multirun/2026-02-19/12-15-36" # invalidate
)

for resdir in "${T1_SYN_RESULT_DIRS[@]}"; do
  python classify_syn.py "${resdir}" --fext csv --benchmark_type t1_attraction
done

for resdir in "${BFCL_SYN_RESULT_DIRS[@]}"; do
  python classify_syn.py "${resdir}" --fext json --benchmark_type bfcl_multiturn_base
done

for resdir in "${ACP_SYN_RESULT_DIRS[@]}"; do
  python classify_syn.py "${resdir}" --fext json --benchmark_type bfcl_multiturn_base
done