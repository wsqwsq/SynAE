import argparse
import json
from pathlib import Path


def load_file(file_path: str):
    result = []
    with open(file_path) as f:
        file = f.readlines()
        for line in file:
            json_line = json.loads(line)
            if "accuracy" not in json_line:
                result.append(json_line)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Get ground truth tool calls for synthetic instructions")
    parser.add_argument("syn_fp", type=str, help="Path to score JSON file")
    parser.add_argument("file_tag", type=str,
                        help="Tag to add to the end of the output filename")
    args = parser.parse_args()

    inferred_data = load_file(args.syn_fp)
    output_dir = Path(args.syn_fp).parent
    fn = Path(args.syn_fp).stem

    extracted_data = []
    for res in inferred_data:
        res_id = res["id"]
        res_tool_calls = res.get("model_result_decoded", [])
        flattened_tool_calls = []
        for turn_steps in res_tool_calls:
            turn_calls = []
            for step_calls in turn_steps:
                turn_calls.extend(step_calls)
            if len(turn_calls) > 0:
                flattened_tool_calls.append(turn_calls)
        extracted_data.append({
            "id": res_id,
            "ground_truth": flattened_tool_calls
        })

    output_fp = f"{output_dir}/{fn}_tool_calls_{args.file_tag}.json"
    with open(output_fp, "w") as f:
        for line in extracted_data:
            json_str = json.dumps(line)
            f.write(json_str + "\n")
    print(f"Saved extracted tool calls to {output_fp}!")
