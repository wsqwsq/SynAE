import argparse
import json

import pandas as pd
import sacrebleu

from apigen_mt_config import APIGenMTConfig, add_config_args, build_config
from apigen_mt_llm import extract_tag, get_backend
from t1.planner.planner_code import make_reasoning_prompt, output_prompt
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

BLUEPRINTS_FP = "../experimental/syn_case_study/attempt4_blueprints.csv"
OUTPUT_FP = "../experimental/syn_case_study/attempt4_aug_inferred.csv"

STOP_TOKEN = "###STOP###"


# arXiv 2504.03601 Figure 11
def build_human_sim_prompt(instruction: str, persona: str, chat_history: list) -> list:
    system_prompt = (
        f"You are a user with this persona: {persona}\n"
        "You are chatting with a travel attraction assistant. Generate one line at a time. Do not give "
        "away all of your goal at once; only provide the information necessary for the current step. "
        "Do not hallucinate information that is not part of your goal. Do not repeat your goal verbatim; "
        "use your own words. Keep the conversation natural and consistent with your persona. "
        f"If your goal is satisfied, reply with exactly {STOP_TOKEN} to end the conversation. "
        "Reply with only your next message, no role prefix."
    )
    user_prompt = f"Your goal: {instruction}\n\nConversation so far:\n{chat_history}\n\nYour next message:"
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]


# arXiv 2504.03601 Figure 12
def build_bon_judge_prompt(instruction: str, persona: str, candidate: str) -> list:
    description = f"Persona: {persona}\nTask: {instruction}"
    system_prompt = "You are a fair judge and an expert in following details."
    user_prompt = f"""
A human is interacting with a travel attraction assistant to get help with their task. You are provided
the description of the human and their task (wrapped with <description></description>), and a candidate
response (wrapped with <response></response>) the human wants to send. Score the candidate response from
0 to 10:
1. If the response includes specific details and they correctly match the task description, give a full
   score of 10; give a lower score for incorrect or changed details.
2. Normal conversational moves (asking for details, saying {STOP_TOKEN}, etc.) are all correct responses.
3. If the response keeps the conversation flowing naturally, give a high score; an unhelpful or evasive
   response should get a lower score.

<description>{description}</description>
<response>{candidate}</response>

Wrap your score in <score></score> tags.
"""
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]


def simulate_human_turn(cfg: APIGenMTConfig, instruction: str, persona: str, chat_history: list) -> str:
    human_sim = get_backend(cfg, "human_sim")
    prompt = build_human_sim_prompt(instruction, persona, chat_history)
    candidates = human_sim.call_batch([prompt] * cfg.human_sim_best_of_n, temperature=cfg.human_sim_temperature)

    if len(candidates) == 1:
        return candidates[0]

    score_prompts = [build_bon_judge_prompt(instruction, persona, c) for c in candidates]
    score_responses = human_sim.call_batch(score_prompts, temperature=0.0)
    scores = []
    for response in score_responses:
        raw = extract_tag(response, "score")
        try:
            scores.append(int(raw))
        except ValueError:
            scores.append(0)
    return candidates[scores.index(max(scores))]


def run_agent_turn(cfg: APIGenMTConfig, chat_history: list) -> str:
    agent = get_backend(cfg, "agent")
    prompt = make_reasoning_prompt(f"{chat_history}", dump_entire_cache())
    response_text = agent.call(prompt, temperature=cfg.agent_temperature)
    code = extract_tag(response_text, "CODE")
    if code:
        try:
            exec(code)
        except Exception:
            pass  # a failed turn just leaves the cache unchanged; validation catches it at the end
    return code


def build_assistant_reply_prompt(chat_history: list, cache: dict) -> list:
    system_prompt = (
        "You are a travel attraction assistant. Reply with a short, natural, in-character message "
        "to the user's latest turn. Do not list full search results here; a final recommendation "
        "message is sent separately at the end of the conversation. Reply with only your message, "
        "no role prefix."
    )
    user_prompt = f"Conversation so far:\n{chat_history}\n\nTool results so far:\n{cache}\n\nYour reply:"
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]


def generate_assistant_reply(cfg: APIGenMTConfig, chat_history: list) -> str:
    agent = get_backend(cfg, "agent")
    prompt = build_assistant_reply_prompt(chat_history, dump_entire_cache())
    return agent.call(prompt, temperature=cfg.agent_temperature)


def collect_trajectory(cfg: APIGenMTConfig, blueprint: dict) -> tuple:
    reset_cache()
    chat_history = [{"assistant": "Hello! Are you looking for something to do in your free time?"}]

    for _ in range(cfg.max_turns):
        user_message = simulate_human_turn(cfg, blueprint["instruction"], blueprint["persona"], chat_history)
        if STOP_TOKEN in user_message:
            break
        chat_history.append({"user": user_message})
        run_agent_turn(cfg, chat_history)
        chat_history.append({"assistant": generate_assistant_reply(cfg, chat_history)})

    final_output_prompt = output_prompt(f"{chat_history}", dump_entire_cache())
    final_output = get_backend(cfg, "agent").call(final_output_prompt, temperature=cfg.agent_temperature)

    data_lines = [f"{role}: {content}" for turn in chat_history for role, content in turn.items()]
    return "\n".join(data_lines), dump_entire_cache(), final_output


def cache_matches_diff_patch(cache: dict, diff_patch: dict) -> bool:
    cache_values = {str(v) for entry in cache.values() for v in (entry if isinstance(entry, list) else [entry])}
    diff_values = {str(v) for entry in diff_patch.values() for v in (entry if isinstance(entry, list) else [entry])}
    return bool(diff_values) and diff_values.issubset(cache_values | {str(cache)})


def outputs_match(cfg: APIGenMTConfig, candidate_output: str, expected_output: str) -> bool:
    score = sacrebleu.sentence_bleu(candidate_output, [expected_output]).score
    return score >= cfg.output_bleu_pass_threshold


def collect_valid_trajectory(cfg: APIGenMTConfig, blueprint: dict) -> tuple | None:
    diff_patch = json.loads(blueprint["diff_patch"])
    for _ in range(cfg.max_trials):
        data, final_cache, final_output = collect_trajectory(cfg, blueprint)
        if cache_matches_diff_patch(final_cache, diff_patch) and outputs_match(cfg, final_output, blueprint["outputs"]):
            return data, blueprint["actions"], final_output
    return None


def main():
    parser = argparse.ArgumentParser(description="Simulate human-agent trajectories for APIGen-MT blueprints")
    add_config_args(parser)
    args = parser.parse_args()
    cfg = build_config(args)

    blueprints_df = pd.read_csv(BLUEPRINTS_FP)

    rows = []
    n_failed = 0
    for i, blueprint in enumerate(blueprints_df.to_dict("records")):
        result = collect_valid_trajectory(cfg, blueprint)
        if result is None:
            n_failed += 1
            continue
        data, tool_call, output = result
        rows.append({"ID": i, "Data": data, "Tool Call": tool_call, "Output": output})

    print(f"Collected {len(rows)} valid trajectories ({n_failed} blueprints failed all trials).")

    aug_df = pd.DataFrame(rows)
    aug_df.to_csv(OUTPUT_FP, index=False)
    print(f"Saved attempt4_aug_inferred to {OUTPUT_FP}!")


if __name__ == "__main__":
    main()
