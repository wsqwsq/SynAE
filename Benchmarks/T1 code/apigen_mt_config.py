import argparse
from dataclasses import asdict, dataclass, field, fields
from typing import List, Literal

import yaml

Backend = Literal["vllm", "openai"]


@dataclass
class APIGenMTConfig:
    backend: Backend = "vllm"  # "vllm" is free/local; switch to "openai" for the real run

    # Interpreted as vLLM model ids or OpenAI model names depending on `backend`
    generator_model: str = "meta-llama/Llama-3.1-8B-Instruct"
    human_sim_model: str = "meta-llama/Llama-3.1-8B-Instruct"
    agent_model: str = "meta-llama/Llama-3.1-8B-Instruct"

    # arXiv 2504.03601 Section 4.1.2 / 4.3
    judge_models: List[str] = field(
        default_factory=lambda: ["meta-llama/Llama-3.1-8B-Instruct", "Qwen/Qwen2.5-7B-Instruct"]
    )

    generator_temperature: float = 0.7
    judge_temperature: float = 0.3
    human_sim_temperature: float = 0.7
    agent_temperature: float = 0.5
    max_tokens: int = 512

    vllm_tensor_parallel_size: int = 1
    vllm_gpu_memory_utilization: float = 0.85  # each engine gets its own GPU by default, see below
    vllm_max_model_len: int = 16384  # caps KV cache reservation well below the model's full context
    # Pool of CUDA_VISIBLE_DEVICES values, one per distinct vLLM engine, cycled if more
    # engines than devices. Indices are relative to whatever's already visible to this
    # process (e.g. if the shell sets CUDA_VISIBLE_DEVICES=1,2, "0" here means physical GPU 1).
    vllm_gpu_devices: List[str] = field(default_factory=lambda: ["0", "1", "2", "3"])

    openai_max_retries: int = 3
    openai_max_workers: int = 8

    # Phase 1
    max_blueprint_iters: int = 3
    judge_committee_size: int = 3
    # arXiv 2504.03601 Figure 9
    judge_pass_threshold: int = 4
    n_fewshot_examples: int = 2
    persona_sample_pool_size: int = 200

    # Phase 2
    max_trials: int = 3  # rejection-sampling attempts per blueprint
    max_turns: int = 8  # matches attempts 1-3's ~6-turn conversations
    human_sim_best_of_n: int = 2
    output_bleu_pass_threshold: float = 15.0  # sentence-BLEU score to accept a trajectory's Output

    seed: int = 123  # matches get_t1_case_study.py's SEED

    @classmethod
    def from_yaml(cls, path: str) -> "APIGenMTConfig":
        with open(path) as f:
            overrides = yaml.safe_load(f) or {}
        valid_fields = {f.name for f in fields(cls)}
        unknown = set(overrides) - valid_fields
        if unknown:
            raise ValueError(f"Unknown APIGenMTConfig field(s) in {path}: {sorted(unknown)}")
        return cls(**overrides)

    def to_dict(self) -> dict:
        return asdict(self)


def add_config_args(parser: argparse.ArgumentParser) -> None:
    """Shared --config/--backend flags for the Attempt 4 scripts."""
    parser.add_argument(
        "--config", type=str, default=None,
        help="Path to a YAML file overriding APIGenMTConfig defaults",
    )
    parser.add_argument(
        "--backend", type=str, choices=["vllm", "openai"], default=None,
        help="Override the config's backend",
    )


def build_config(args: argparse.Namespace) -> APIGenMTConfig:
    cfg = APIGenMTConfig.from_yaml(args.config) if args.config else APIGenMTConfig()
    if args.backend:
        cfg.backend = args.backend
    return cfg
