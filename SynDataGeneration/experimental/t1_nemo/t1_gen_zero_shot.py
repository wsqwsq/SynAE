import logging

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


def chat_conv_to_text(conv):
    if not isinstance(conv, ChatConversation):
        conv = ChatConversation(**conv)

    conv_text_lines = []
    for m in conv.conversation:
        turn_text = f"{m.role}: {m.content}"
        conv_text_lines.append(turn_text)
    conv_text = "\n".join(conv_text_lines)
    return conv_text


@hydra.main(version_base=None, config_path="model_configs", config_name="config")
def main(cfg: DictConfig) -> None:
    output_dir = hydra.core.hydra_config.HydraConfig.get().runtime.output_dir
    log.info(f"Running with config:\n{cfg}")
    log.info(f"Output will be saved to: {output_dir}")

    # Save orig df in output dir
    orig_df = pd.read_csv("orig_df.csv")
    orig_df.to_csv(f"{output_dir}/orig_df.csv", index=False)

    # Set up data designer according to their tutorial
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
                timeout=cfg.model.timeout if cfg.model.timeout is not None else 60
            ),
        )
    ]
    config_builder = DataDesignerConfigBuilder(model_configs=model_configs)

    # Load t1 data to get the number of synthetic samples required
    orig_df_proc = pd.read_csv("orig_df_proc.csv")
    n_samples = len(orig_df_proc)
    orig_df_proc.to_csv(f"{output_dir}/orig_df_proc.csv", index=False)

    # Load valid attraction types from the ontology
    ont = get_t1_attraction_ontology()
    valid_types = ont["types"]

    # Add t1 attraction type column to the config builder
    config_builder.add_column(
        SamplerColumnConfig(
            name="type",
            sampler_type=SamplerType.CATEGORY,
            params=CategorySamplerParams(values=valid_types),
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

    # Generate synthetic data
    job_results = data_designer_client.create(config_builder, num_records=n_samples)
    job_results.wait_until_done()
    syn_df_proc = job_results.load_dataset()

    # Add ID column (required by t1)
    syn_df_proc["ID"] = list(range(len(syn_df_proc)))

    # Make the conversation column a newline separated text field
    syn_df_proc["Filled_Template"] = syn_df_proc["Filled_Template"].apply(
        chat_conv_to_text
    )

    # Keep only the required columns
    syn_df_proc = syn_df_proc[["ID", "Filled_Template"]]

    # Save synthetic data
    syn_df_proc.to_csv(f"{output_dir}/syn_df_proc.csv", index=False)

    # Post-process synthetic data
    syn_df, _ = postprocess(syn_df_proc)
    syn_df.to_csv(f"{output_dir}/syn_df.csv", index=False)


if __name__ == "__main__":
    main()
