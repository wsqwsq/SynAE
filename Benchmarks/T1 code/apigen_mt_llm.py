import os
import re
from typing import List, Protocol

from dotenv import load_dotenv
from openai import OpenAI
from tqdm.contrib.concurrent import thread_map

from apigen_mt_config import APIGenMTConfig

load_dotenv()


class LLMBackend(Protocol):
    def call(self, messages: List[dict], temperature: float = 0.7) -> str: ...

    def call_batch(self, list_of_messages: List[List[dict]], temperature: float = 0.7) -> List[str]: ...


class OpenAIBackend:
    def __init__(self, model: str, max_retries: int = 3, max_workers: int = 8):
        self.model = model
        self.max_retries = max_retries
        self.max_workers = max_workers
        self.client = OpenAI()

    def call(self, messages: List[dict], temperature: float = 0.7) -> str:
        last_error = None
        for _ in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model, messages=messages, temperature=temperature,
                )
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
        raise last_error

    def call_batch(self, list_of_messages: List[List[dict]], temperature: float = 0.7) -> List[str]:
        return thread_map(
            lambda messages: self.call(messages, temperature),
            list_of_messages,
            max_workers=self.max_workers,
        )


class VLLMBackend:
    def __init__(self, model: str, tensor_parallel_size: int = 1, max_tokens: int = 512,
                 gpu_memory_utilization: float = 0.9, max_model_len: int = 8192):
        from vllm import LLM, SamplingParams

        self.llm = LLM(
            model=model,
            tensor_parallel_size=tensor_parallel_size,
            gpu_memory_utilization=gpu_memory_utilization,
            max_model_len=max_model_len,
        )
        self.SamplingParams = SamplingParams
        self.max_tokens = max_tokens

    def call(self, messages: List[dict], temperature: float = 0.7) -> str:
        return self.call_batch([messages], temperature)[0]

    def call_batch(self, list_of_messages: List[List[dict]], temperature: float = 0.7) -> List[str]:
        sampling_params = self.SamplingParams(temperature=temperature, max_tokens=self.max_tokens)
        outputs = self.llm.chat(list_of_messages, sampling_params, use_tqdm=True)
        return [o.outputs[0].text.strip() for o in outputs]


# Keyed by (backend, model) so multiple roles pointed at the same model
# (the default config) share one loaded vLLM engine instead of reloading it.
_backend_cache: dict = {}
_vllm_engine_count = 0


def _get_or_create_backend(cfg: APIGenMTConfig, model: str) -> LLMBackend:
    cache_key = (cfg.backend, model)
    if cache_key in _backend_cache:
        return _backend_cache[cache_key]

    if cfg.backend == "openai":
        backend = OpenAIBackend(model, max_retries=cfg.openai_max_retries, max_workers=cfg.openai_max_workers)
    elif cfg.backend == "vllm":
        global _vllm_engine_count
        device = cfg.vllm_gpu_devices[_vllm_engine_count % len(cfg.vllm_gpu_devices)]
        _vllm_engine_count += 1
        os.environ["CUDA_VISIBLE_DEVICES"] = device

        backend = VLLMBackend(
            model,
            tensor_parallel_size=cfg.vllm_tensor_parallel_size,
            max_tokens=cfg.max_tokens,
            gpu_memory_utilization=cfg.vllm_gpu_memory_utilization,
            max_model_len=cfg.vllm_max_model_len,
        )
    else:
        raise ValueError(f"Unknown backend: {cfg.backend}")

    _backend_cache[cache_key] = backend
    return backend


def get_backend(cfg: APIGenMTConfig, role: str) -> LLMBackend:
    return _get_or_create_backend(cfg, getattr(cfg, f"{role}_model"))


def get_judge_backends(cfg: APIGenMTConfig) -> List[LLMBackend]:
    return [_get_or_create_backend(cfg, model) for model in cfg.judge_models]


def extract_tag(text: str, tag: str) -> str:
    if not text:
        return ""
    match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    return match.group(1).strip() if match else ""
