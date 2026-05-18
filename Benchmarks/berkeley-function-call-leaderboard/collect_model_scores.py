import argparse
import json
import re
from pathlib import Path

import pandas as pd


def collect_scores(score_dir: Path) -> pd.DataFrame:
    rows = []
    for score_file in sorted(score_dir.glob("*/multi_turn/BFCL_v4_*_score.json")):
        # Skip syn_tc files
        if score_file.stem.endswith("_tool_calls_syn_tc"):
            continue

        model = score_file.parts[-3]
        # Strip BFCL_v4_ prefix and _score suffix
        test_category = re.sub(r"^BFCL_v4_", "", score_file.stem)
        test_category = re.sub(r"_score$", "", test_category)

        with open(score_file) as f:
            first_line = f.readline()
        data = json.loads(first_line)

        rows.append({
            "model": model,
            "test_category": test_category,
            "accuracy": data["accuracy"],
            "correct_count": data["correct_count"],
            "total_count": data["total_count"],
        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Collect BFCL scores into a CSV.")
    parser.add_argument("--score-dir", default="score",
                        help="Path to score directory")
    parser.add_argument("--output", default="scores.csv",
                        help="Output CSV file")
    args = parser.parse_args()

    score_dir = Path(args.score_dir)
    df = collect_scores(score_dir)
    df.to_csv(args.output, index=False)
    print(f"Saved {len(df)} rows to {args.output}")
