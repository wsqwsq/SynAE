from dataclasses import dataclass
from enum import Enum
from typing import Optional


class BenchmarkType(Enum):
    T1_ATTRACTION = "t1_attraction"
    BFCL_MULTITURN_BASE = "bfcl_multiturn_base"
    ACP_APP_PROG = "acp_app_prog"


class GenMethodType(Enum):
    OVERSAMPLE = "oversample"
    BLANKFILL = "blankfill"
    FEWSHOT = "fewshot"
    DROPMIN = "dropmin"
    INVALIDATE = "invalidate"


@dataclass
class GenParams:
    pass


@dataclass
class OversampleGenParams(GenParams):
    dup_sample_idxs: list[int]
    dup_frac: float
    with_replacement: bool = True
    seed: Optional[int] = None


@dataclass
class BlankfillGenParams(GenParams):
    blank_probability: float
    hf_llm_gen_args: dict
    seed: Optional[int] = None


@dataclass
class FewshotGenParams(GenParams):
    n_examples: int
    hf_llm_gen_args: dict
    seed: Optional[int] = None


@dataclass
class DropMinGenParams(GenParams):
    class_df_fp = str
    min_class_name: str
    drop_n_min: int
    drop_per_class_frac: float = 0.3
    seed: Optional[int] = None


@dataclass
class InvalidateGenParams(GenParams):
    invalidate_frac: float = 0.3
    seed: Optional[int] = None


@dataclass
class OrigDataConfig:
    benchmark_type: BenchmarkType
    filepaths: list[str]


@dataclass
class SynDataConfig:
    gen_method_type: GenMethodType
    gen_params: GenParams


@dataclass
class Config:
    orig_data: OrigDataConfig
    syn_data: SynDataConfig
