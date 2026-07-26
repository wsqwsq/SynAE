import argparse
import json
import re

import numpy as np
import pandas as pd
from datasets import load_dataset

from apigen_mt_config import APIGenMTConfig, add_config_args, build_config
from apigen_mt_llm import extract_tag, get_backend, get_judge_backends
from t1.planner.planner_code import all_tools_config
from t1.tools.cache import (
    dump_entire_cache,
    get_results_from_cache,
    reset_cache,
    save_to_cache,
)
from t1.tools.filter_attractions import filter_attractions
from t1.tools.find_nearest import search_nearest
from t1.tools.search_attractions import search_attractions
from t1.tools.sort_results import sort_results

EXPERIMENTAL_DIR = "../experimental"
DROPPED_INFO_FP = f"{EXPERIMENTAL_DIR}/syn_case_study/dropped_info.json"
ORIG_VALID_FP = f"{EXPERIMENTAL_DIR}/orig_valid.csv"
ONTOLOGY_FP = f"{EXPERIMENTAL_DIR}/ontology_t1_attraction_data.csv"
OUTPUT_FP = f"{EXPERIMENTAL_DIR}/syn_case_study/attempt4_blueprints.csv"


def get_type(data: str, types: list) -> str | None:
    for t in types:
        if re.search(rf"\b{re.escape(t)}\b", data):
            return t
    return None


def load_personas(pool_size: int, rng: np.random.Generator) -> list:
    dataset = load_dataset("proj-persona/PersonaHub", "persona", split="train")
    idxs = rng.choice(len(dataset), size=pool_size, replace=False)
    return [dataset[int(i)]["persona"] for i in idxs]


def build_fewshot_examples(orig_valid_df: pd.DataFrame, attraction_type: str, types: list, n: int, rng) -> list:
    type_series = orig_valid_df["Data"].apply(lambda d: get_type(d, types))
    matching_idxs = orig_valid_df.index[type_series == attraction_type].tolist()
    if not matching_idxs:
        return []
    chosen = rng.choice(matching_idxs, size=min(n, len(matching_idxs)), replace=False)

    examples = []
    for idx in chosen:
        row = orig_valid_df.loc[idx]
        user_lines = [ln for ln in row["Data"].split("\n") if ln.lower().startswith("user:")]
        examples.append({
            "instruction": " ".join(user_lines),
            "actions": row["Tool Call"],
            "outputs": row["Output"],
        })
    return examples


def sample_context(attraction_type: str, ontology_df: pd.DataFrame, orig_valid_df: pd.DataFrame,
                    types: list, personas: list, cfg: APIGenMTConfig, rng) -> dict:
    type_rows = ontology_df[ontology_df["type"] == attraction_type]
    location_row = type_rows.sample(n=1, random_state=int(rng.integers(1_000_000))).iloc[0]

    return {
        "attraction_type": attraction_type,
        "city": location_row["city"],
        "state": location_row["state"],
        "neighborhood": location_row["neighborhood"],
        "persona": personas[int(rng.integers(len(personas)))],
        "fewshot_examples": build_fewshot_examples(orig_valid_df, attraction_type, types, cfg.n_fewshot_examples, rng),
    }


def build_generator_prompt(context: dict, feedback: str | None = None) -> list:
    fewshot_text = "\n\n".join(
        f"Instruction: {ex['instruction']}\nActions:\n{ex['actions']}\nOutputs: {ex['outputs']}"
        for ex in context["fewshot_examples"]
    )

    system_prompt = (
        "You are a task designer for an AI travel attraction assistant. "
        "You generate a single verifiable task blueprint: a user instruction, the exact "
        "tool-call code that fulfills it, and the expected final output."
    )

    user_prompt = f"""
# TOOLS AVAILABLE
{all_tools_config}

# TASK CONTEXT
- Attraction type: {context["attraction_type"]}
- City: {context["city"]}, State: {context["state"]}
- Neighborhood: {context["neighborhood"]}
- User persona: {context["persona"]}

# EXAMPLES OF WELL-FORMED BLUEPRINTS
{fewshot_text}

# INSTRUCTIONS
- Do not fabricate entity values; use the city/state/neighborhood/type given above exactly as written.
- The actions must be valid Python code calling only the tools listed above, using save_to_cache/get_results_from_cache
  the same way the examples do.
- Output your response in exactly these four tags:
<THOUGHT>your reasoning for this task design</THOUGHT>
<INSTRUCTION>the user's high-level request, written as a first-person message</INSTRUCTION>
<ACTIONS>python code fulfilling the instruction</ACTIONS>
<OUTPUTS>the expected final assistant response to the user</OUTPUTS>
"""

    if feedback:
        user_prompt += f"\n# FEEDBACK ON YOUR PREVIOUS ATTEMPT\n{feedback}\nRevise the blueprint to address this feedback.\n"

    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]


def parse_blueprint(response_text: str) -> dict:
    return {
        "thought": extract_tag(response_text, "THOUGHT"),
        "instruction": extract_tag(response_text, "INSTRUCTION"),
        "actions": extract_tag(response_text, "ACTIONS"),
        "outputs": extract_tag(response_text, "OUTPUTS"),
    }


def exec_actions(actions_code: str) -> tuple:
    reset_cache()
    try:
        exec(actions_code)
    except Exception as e:
        return False, str(e), None
    return True, None, dump_entire_cache()


# arXiv 2504.03601 Figure 9
JUDGE_CRITERIA = ("correctness", "completeness", "satisfaction", "creativity")


def build_judge_prompt(blueprint: dict, diff_patch: dict) -> list:
    system_prompt = "You are a strict reviewer of AI agent task designs for a travel attraction assistant."

    user_prompt = f"""
# TASK BLUEPRINT
Instruction: {blueprint["instruction"]}
Actions:
{blueprint["actions"]}
Expected outputs: {blueprint["outputs"]}
Resulting tool state (diff_patch): {diff_patch}

# RUBRIC
Score each dimension 0 (does not follow) or 1 (follows):
- Correctness: do the actions accurately implement the instruction?
- Completeness: is the instruction sufficiently detailed, and is it fully addressed by the actions?
- Satisfaction: do the expected outputs fulfill any explicit or implicit information requests within the instruction?
- Creativity: does the task represent a non-trivial, plausible, and potentially interesting scenario?

Respond in exactly these tags:
<CORRECTNESS>0 or 1</CORRECTNESS>
<COMPLETENESS>0 or 1</COMPLETENESS>
<SATISFACTION>0 or 1</SATISFACTION>
<CREATIVITY>0 or 1</CREATIVITY>
<FEEDBACK>one or two sentences of concrete feedback, empty if no issues</FEEDBACK>
"""

    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]


def parse_judge_response(response_text: str) -> dict:
    scores = {}
    for criterion in JUDGE_CRITERIA:
        raw = extract_tag(response_text, criterion.upper())
        scores[criterion] = 1 if raw.strip() == "1" else 0
    scores["feedback"] = extract_tag(response_text, "FEEDBACK")
    return scores


def majority_vote(judge_scores: list) -> dict:
    votes = {}
    for criterion in JUDGE_CRITERIA:
        yes_votes = sum(s[criterion] for s in judge_scores)
        votes[criterion] = 1 if yes_votes > len(judge_scores) / 2 else 0
    votes["total"] = sum(votes[c] for c in JUDGE_CRITERIA)
    return votes


def run_committee(cfg: APIGenMTConfig, blueprint: dict, diff_patch: dict) -> tuple:
    prompt = build_judge_prompt(blueprint, diff_patch)
    judge_backends = get_judge_backends(cfg)

    judge_scores = []
    for i, judge in enumerate(judge_backends):
        n_calls = cfg.judge_committee_size // len(judge_backends)
        if i < cfg.judge_committee_size % len(judge_backends):
            n_calls += 1
        responses = judge.call_batch([prompt] * n_calls, temperature=cfg.judge_temperature)
        judge_scores.extend(parse_judge_response(r) for r in responses)

    votes = majority_vote(judge_scores)
    passed = votes["total"] >= cfg.judge_pass_threshold

    feedback = " ".join(s["feedback"] for s in judge_scores if s["feedback"])
    return passed, votes["total"], feedback


def generate_blueprint(cfg: APIGenMTConfig, context: dict) -> dict | None:
    generator = get_backend(cfg, "generator")
    feedback = None

    for n_iters in range(1, cfg.max_blueprint_iters + 1):
        prompt = build_generator_prompt(context, feedback)
        response_text = generator.call(prompt, temperature=cfg.generator_temperature)
        blueprint = parse_blueprint(response_text)

        if not all(blueprint.values()):
            feedback = "Response was missing one or more required tags."
            continue

        success, exec_error, diff_patch = exec_actions(blueprint["actions"])
        if not success:
            feedback = f"Actions failed to execute: {exec_error}"
            continue

        passed, judge_total, judge_feedback = run_committee(cfg, blueprint, diff_patch)
        if passed:
            return {
                **context,
                **blueprint,
                "diff_patch": json.dumps(diff_patch, default=str),
                "judge_total": judge_total,
                "n_iters": n_iters,
            }
        feedback = judge_feedback or "Reviewers scored this blueprint below the pass threshold."

    return None


def main():
    parser = argparse.ArgumentParser(description="Generate APIGen-MT task blueprints for dropped attraction types")
    add_config_args(parser)
    args = parser.parse_args()
    cfg = build_config(args)

    rng = np.random.default_rng(cfg.seed)

    with open(DROPPED_INFO_FP) as f:
        dropped_info = json.load(f)
    ontology_df = pd.read_csv(ONTOLOGY_FP)
    orig_valid_df = pd.read_csv(ORIG_VALID_FP)
    types = ontology_df["type"].unique().tolist()

    print(f"Loading {cfg.persona_sample_pool_size} personas from PersonaHub...")
    personas = load_personas(cfg.persona_sample_pool_size, rng)

    weighted_types = [t for t, n_to_add in dropped_info for _ in range(n_to_add)]
    print(f"Generating {len(weighted_types)} blueprints across {len(dropped_info)} dropped types...")

    blueprints = []
    n_failed = 0
    for i, attraction_type in enumerate(weighted_types):
        context = sample_context(attraction_type, ontology_df, orig_valid_df, types, personas, cfg, rng)
        blueprint = generate_blueprint(cfg, context)
        if blueprint is None:
            n_failed += 1
            continue
        blueprint["ID"] = i
        blueprints.append(blueprint)

    print(f"Generated {len(blueprints)} valid blueprints ({n_failed} dropped after exhausting retries).")

    blueprints_df = pd.DataFrame(blueprints)
    blueprints_df.to_csv(OUTPUT_FP, index=False)
    print(f"Saved blueprints to {OUTPUT_FP}!")


if __name__ == "__main__":
    main()
