import logging
import re
from typing import Optional

import hydra
import pandas as pd
from omegaconf import DictConfig
from nemo_microservices.data_designer.essentials import (
    CategorySamplerParams,
    DataDesignerConfigBuilder,
    InferenceParameters,
    LLMStructuredColumnConfig,
    ModelConfig,
    NeMoDataDesignerClient,
    SamplerColumnConfig,
    SamplerType,
)

from utils import (
    ChatConversation,
    get_t1_attraction_ontology,
    postprocess,
)

log = logging.getLogger(__name__)

ORIG_VALID_FP = "orig_valid.csv"
BASE_FP = "base.csv"


def get_type(data: str, types: list) -> Optional[str]:
    for t in types:
        if re.search(rf"\b{re.escape(t)}\b", data):
            return t
    return None


def compute_n_to_add(base_df: pd.DataFrame, orig_df: pd.DataFrame, types: list) -> dict:
    base_counts = base_df["Data"].apply(lambda d: get_type(d, types)).value_counts()
    orig_counts = orig_df["Data"].apply(lambda d: get_type(d, types)).value_counts()

    n_to_add = {}
    for t in types:
        diff = orig_counts.get(t, 0) - base_counts.get(t, 0)
        if diff > 0:
            n_to_add[t] = diff
    return n_to_add


def chat_conv_to_text(conv):
    if not isinstance(conv, ChatConversation):
        conv = ChatConversation(**conv)

    conv_text_lines = []
    for m in conv.conversation:
        turn_text = f"{m.role}: {m.content}"
        conv_text_lines.append(turn_text)
    return "\n".join(conv_text_lines)


@hydra.main(version_base=None, config_path="model_configs", config_name="config")
def main(cfg: DictConfig) -> None:
    output_dir = hydra.core.hydra_config.HydraConfig.get().runtime.output_dir
    log.info(f"Running with config:\n{cfg}")
    log.info(f"Output will be saved to: {output_dir}")

    orig_df = pd.read_csv(ORIG_VALID_FP)
    base_df = pd.read_csv(BASE_FP)
    orig_df.to_csv(f"{output_dir}/orig_df.csv", index=False)
    base_df.to_csv(f"{output_dir}/base_df.csv", index=False)

    ont = get_t1_attraction_ontology()
    valid_types = ont["types"]

    n_to_add = compute_n_to_add(base_df, orig_df, valid_types)
    log.info(f"Dropped types and counts to generate: {n_to_add}")

    if not n_to_add:
        log.warning("No dropped types found. Exiting.")
        return

    # Repeat each type by its count so the sampler is weighted proportionally
    weighted_types = [t for t, count in n_to_add.items() for _ in range(count)]
    n_samples = int(sum(n_to_add.values()))
    log.info(f"Generating {n_samples} total samples across {len(n_to_add)} types.")

    NEMO_MICROSERVICES_BASE_URL = "http://localhost:8080"
    data_designer_client = NeMoDataDesignerClient(base_url=NEMO_MICROSERVICES_BASE_URL)

    model_configs = [
        ModelConfig(
            alias=cfg.model.model_alias,
            model=cfg.model.model_id,
            provider=cfg.model.model_provider,
            inference_parameters=InferenceParameters(
                temperature=cfg.model.temperature,
                top_p=cfg.model.top_p,
                max_tokens=cfg.model.max_tokens,
                timeout=cfg.model.timeout if cfg.model.timeout is not None else 60,
            ),
        )
    ]
    config_builder = DataDesignerConfigBuilder(model_configs=model_configs)

    config_builder.add_column(
        SamplerColumnConfig(
            name="type",
            sampler_type=SamplerType.CATEGORY,
            params=CategorySamplerParams(values=weighted_types),
        )
    )

    config_builder.add_column(
        LLMStructuredColumnConfig(
            name="Filled_Template",
            prompt="""
Generate a multi-turn conversation between a travel attraction recommendation assistant and a user.
The user is seeking attractions of {{type}} in a specific US state or city.

Diversity requirements - vary each of these across generated conversations:

Assistant behavior:
- Use one distinct personality per conversation: formal, casual, verbose, or concise.
- First turn must be a generic greeting that does not assume user intent (e.g., "How can I help you?").
- Do not say the assistant has found options for the user.
- Occasionally have the assistant correct a user misunderstanding.
- Vary how information is requested: direct questions vs. open-ended prompts.

User behavior:
- Use one user type per conversation: impatient, polite, verbose, or terse.
- Some users provide minimal info and require follow-up; others dump too much detail upfront.
- Some users ask multiple questions at once; some change their minds mid-conversation.

Conversation flow:
- Avoid the standard "greeting -> location -> type -> options" structure.
- Allow nonlinear flows: users circling back, skipping obvious steps, or raising new topics late.
- Vary the order in which location, attraction type, and preferences are elicited.
- Each conversation should have 6 turns.
""",
            output_format=ChatConversation,
            model_alias=cfg.model.model_alias,
            system_prompt=cfg.model.system_prompt,
        )
    )

    config_builder.validate()

    job_results = data_designer_client.create(config_builder, num_records=n_samples)
    job_results.wait_until_done()
    syn_df_proc = job_results.load_dataset()

    syn_df_proc["ID"] = list(range(len(syn_df_proc)))
    syn_df_proc["Filled_Template"] = syn_df_proc["Filled_Template"].apply(chat_conv_to_text)
    syn_df_proc = syn_df_proc[["ID", "Filled_Template"]]
    syn_df_proc.to_csv(f"{output_dir}/syn_df_proc.csv", index=False)

    syn_df, _ = postprocess(syn_df_proc)
    syn_df.to_csv(f"{output_dir}/syn_df.csv", index=False)


if __name__ == "__main__":
    main()
