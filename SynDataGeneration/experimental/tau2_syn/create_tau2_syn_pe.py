"""
This example follows the experimental settings of the GPT-2 PubMed experiments in the ICML 2024 Spotlight paper,
"Differentially Private Synthetic Data via Foundation Model APIs 2: Text" (https://arxiv.org/abs/2403.01749).

The ``model_name_or_path`` parameter can be set to other models on HuggingFace. Note that we use the FastChat
library (https://github.com/lm-sys/FastChat) to manage the conversation template. If the conversation template of your
desired model is not available in FastChat, please register the conversation template in the FastChat library. See the
following link for an example:
https://github.com/microsoft/DPSDA/blob/main/pe/llm/huggingface/register_fastchat/gpt2.py

The saved CSV files contain both the text selected by the histogram and the generated variations of the selected text,
while the original paper (https://arxiv.org/abs/2403.01749) only use the text selected by the histogram for downstream
evaluation. We can extract the desired text from the saved checkpoints; please see
https://microsoft.github.io/DPSDA/getting_started/examples.html#checkpoint-operation
for more details.

For detailed information about parameters and APIs, please consult the documentation of the Private Evolution library:
https://microsoft.github.io/DPSDA/.
"""

from pe.data import TextCSV
from pe.logging import setup_logging
from pe.runner import PE
from pe.population import PEPopulation
from pe.api.text import LLMAugPE
from pe.llm import HuggingfaceLLM
from pe.embedding.text import SentenceTransformer
from pe.histogram import NearestNeighbors
from pe.callback import SaveCheckpoints
from pe.callback import ComputeFID
from pe.callback import SaveTextToCSV
from pe.logger import CSVPrint
from pe.logger import LogPrint
from pe.constant.data import VARIATION_API_FOLD_ID_COLUMN_NAME

import json
import pandas as pd
import os
import numpy as np
import yaml

pd.options.mode.copy_on_write = True


random_prompt = {
    "message_template": [
        {
            "role": "user",
            "content": """Generate a synthetic test case in YAML format for testing a task management assistant API.

The test case YAML must follow this EXACT structure with ALL keys present:

id: <unique_test_id>
description:
  purpose: <what functionality is being tested>
  notes: <additional context about the test>
user_scenario:
  persona: <optional: communication style description>
  instructions: <detailed scenario instructions>
ticket: <brief description of what the user needs>
initial_state:
  message_history: []
  initialization_data: {{}}
  initialization_actions: []
evaluation_criteria:
  actions:
    - action_id: <action_id>
      name: <function_name>
      arguments: {{}}
      compare_args: []
      info: <description of what this action does>
  env_assertions: []
  nl_assertions: []
  communicate_info: []
  reward_basis: []

Valid function names: create_task, update_task_status, delete_task, get_task, list_tasks, transfer_to_human_agents

Common test scenarios:
- Creating tasks (meetings, projects, deadlines, reminders)
- Updating task status (pending -> completed, in_progress, etc.)
- Impossible requests that should transfer to human agents
- Multi-step workflows with message history
- Tasks with environment assertions

Guidelines:
- id follows patterns: create_task_X, update_task_X, impossible_task_X, etc.
- persona describes communication style or can be omitted
- instructions are detailed scenario descriptions
- ticket is a 1-2 sentence summary
- initial_state fields can be empty if not needed
- actions typically has 1-2 actions
- nl_assertions describe expected agent confirmations
- reward_basis examples: [DB, ACTION], [ENV_ASSERTION], [DB, ENV_ASSERTION]

Create a realistic test case. Respond with ONLY the test case YAML, no other text.
Stop generation after completing the YAML structure.""",
        },
    ]
}

variation_prompt = {
    "message_template": [
        {
            "role": "user",
            "content": """Create a variation of this test case. You must:
1. Keep the EXACT same YAML structure and ALL keys
2. Preserve all field names in arguments, initial_state, and evaluation_criteria
3. {variation_instruction}

Input YAML:
{sample}

Rules:
- Do NOT change: id pattern (e.g., keep create_task in id if present), function names in actions, key names in arguments
- DO change: specific values like task titles, descriptions, user scenarios, personas, test purposes
- Maintain realism and coherence
- Keep the same general test type (create/update/delete/impossible)

Respond with ONLY the modified YAML, no markdown, no explanations.
Stop generation after completing the YAML structure.""",
        },
    ],
    "replacement_rules": [
        {
            "constraints": {},
            "replacements": {
                "variation_instruction": [
                    "modify the scenario details while keeping the same test type and structure",
                    "rephrase all text content with different wording but similar meaning",
                    "change the specific task details (titles, descriptions) while maintaining test intent",
                    "rewrite the user scenario and persona with a different style",
                    "create alternative versions of descriptions and instructions",
                    "paraphrase all text fields using varied vocabulary and sentence structures",
                    "generate a different but equivalent test scenario",
                    "modify content to create diversity while preserving functionality being tested",
                ]
            },
        }
    ],
}

with open("random_api_prompt.json", "w") as f:
    json.dump(random_prompt, f, indent=2)

with open("variation_api_prompt.json", "w") as f:
    json.dump(variation_prompt, f, indent=2)


def tau2_json_to_df(json_data) -> pd.DataFrame:
    """Convert JSON test cases to DataFrame with YAML strings for PE processing."""
    df = pd.DataFrame(
        {
            "text": [
                yaml.dump(obj, default_flow_style=False, sort_keys=False)
                for obj in json_data
            ]
        }
    )
    return df


if __name__ == "__main__":
    exp_folder = "results/text/tau2_syn"
    current_folder = os.path.dirname(os.path.abspath(__file__))

    setup_logging(log_file=os.path.join(exp_folder, "log.txt"))

    tau2_json = json.load(open("tau2_mock_tasks.json", "r"))
    tau2_df = tau2_json_to_df(tau2_json)
    tau2_df.to_csv("tau2_mock_tasks.csv", index=False)
    data = TextCSV(csv_path="tau2_mock_tasks.csv")

    # hf_model_name = "gpt2"
    # llm = HuggingfaceLLM(
    #     max_completion_tokens=448, model_name_or_path=hf_model_name, temperature=1.0
    # )
    llm = HuggingfaceLLM(
        max_completion_tokens=1000,
        batch_size=8,
        model_name_or_path="meta-llama/Llama-3.1-8B-Instruct",
        temperature=0.5,
    )
    api = LLMAugPE(
        llm=llm,
        random_api_prompt_file=os.path.join(current_folder, "random_api_prompt.json"),
        variation_api_prompt_file=os.path.join(
            current_folder, "variation_api_prompt.json"
        ),
    )
    embedding = SentenceTransformer(model="sentence-t5-base")
    histogram = NearestNeighbors(
        embedding=embedding,
        mode="L2",
        lookahead_degree=0,
    )
    population = PEPopulation(
        api=api,
        initial_variation_api_fold=6,
        next_variation_api_fold=6,
        keep_selected=True,
        selection_mode="rank",
    )

    save_checkpoints = SaveCheckpoints(os.path.join(exp_folder, "checkpoint"))
    compute_fid = ComputeFID(
        priv_data=data,
        embedding=embedding,
        filter_criterion={VARIATION_API_FOLD_ID_COLUMN_NAME: -1},
    )
    save_text_to_csv = SaveTextToCSV(
        output_folder=os.path.join(exp_folder, "synthetic_text")
    )

    csv_print = CSVPrint(output_folder=exp_folder)
    log_print = LogPrint()

    num_private_samples = len(data.data_frame)
    delta = 1.0 / num_private_samples / np.log(num_private_samples)

    pe_runner = PE(
        priv_data=data,
        population=population,
        histogram=histogram,
        callbacks=[save_checkpoints, save_text_to_csv, compute_fid],
        loggers=[csv_print, log_print],
    )
    pe_runner.run(
        num_samples_schedule=[25] * 11,
        delta=delta,
        noise_multiplier=0.5,
        # epsilon=1.0,
        checkpoint_path=os.path.join(exp_folder, "checkpoint"),
    )
