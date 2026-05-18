import hydra
import logging

from hydra.core.config_store import ConfigStore
from omegaconf import OmegaConf


from config import BenchmarkType, GenMethodType, Config

from benchmarks.t1_attraction import PIPELINE as T1_PIPELINE
from benchmarks.bfcl_multiturn_base import PIPELINE as BFCL_PIPELINE
from benchmarks.acp_app_prog import PIPELINE as ACP_PIPELINE

log = logging.getLogger(__name__)


# A pipeline contains benchmark-specific code for the following:
# 1. Loading original data from files
# 2. Pre-processing original data for our synthetic data generation pipeline
# 3. Post-processing synthetic data to the original data format
# 4. Saving synthetic data as files
# 5. Any synthetic data generation code that's specific to the benchmark, e.g., blankfilling.
# The code can be found in the benchmarks sub-package.
BENCHMARK_PIPELINES = {
    BenchmarkType.T1_ATTRACTION.value: T1_PIPELINE,
    BenchmarkType.BFCL_MULTITURN_BASE.value: BFCL_PIPELINE,
    BenchmarkType.ACP_APP_PROG.value: ACP_PIPELINE,
}

cs = ConfigStore.instance()
cs.store(name="sb_config", node=Config)


def oversample_gen():
    raise NotImplementedError(
        "Please implement oversample_gen in the benchmark-specific pipeline code."
    )


def blankfill_gen():
    raise NotImplementedError(
        "Please implement blankfill_gen in the benchmark-specific pipeline code."
    )


def fewshot_gen():
    raise NotImplementedError(
        "Please implement fewshot_gen in the benchmark-specific pipeline code."
    )


def dropmin_gen():
    raise NotImplementedError(
        "Please implement dropmin_gen in the benchmark-specific pipeline code."
    )


def invalidate_gen():
    raise NotImplementedError(
        "Please implement invalidate_gen in the benchmark-specific pipeline code."
    )


@hydra.main(version_base=None, config_path="configs_syn", config_name="config")
def main(cfg: Config) -> None:
    log.info(f"Running experiment with settings:\n{OmegaConf.to_yaml(cfg)}")

    output_dir = hydra.core.hydra_config.HydraConfig.get().runtime.output_dir
    log.info(f"Output will be saved to:{output_dir}")

    benchmark_type = cfg.orig_data.benchmark_type

    log.info(f"Using pipeline for benchmark: {benchmark_type}")
    pipeline = BENCHMARK_PIPELINES[benchmark_type]

    # Load original data files based on benchmark type
    log.info("Loading original data from files...")
    orig_df = pipeline["load"](cfg.orig_data.filepaths)
    pipeline["save"](orig_df, fn=f"{output_dir}/orig_df")

    # Pre-process original data based on benchmark type and generation method
    # type to fit our synthetic generation pipeline
    log.info("Pre-processing original data...")
    orig_df_proc = pipeline["preprocess"](orig_df)
    pipeline["save"](orig_df_proc, fn=f"{output_dir}/orig_df_proc")

    # Generate synthetic data according to generation method
    log.info("Generating synthetic data from original data...")
    gen_method_type = cfg.syn_data.gen_method_type
    gen_params = cfg.syn_data.gen_params
    if gen_method_type == GenMethodType.OVERSAMPLE.value:
        syn_df_proc = pipeline["oversample_gen"](df=orig_df_proc, params=gen_params)
    elif gen_method_type == GenMethodType.BLANKFILL.value:
        syn_df_proc = pipeline["blankfill_gen"](df=orig_df_proc, params=gen_params)
    elif gen_method_type == GenMethodType.FEWSHOT.value:
        syn_df_proc = pipeline["fewshot_gen"](df=orig_df_proc, params=gen_params)
    elif gen_method_type == GenMethodType.DROPMIN.value:
        syn_df_proc = pipeline["dropmin_gen"](df=orig_df_proc, params=gen_params)
    elif gen_method_type == GenMethodType.INVALIDATE.value:
        syn_df_proc = pipeline["invalidate_gen"](df=orig_df_proc, params=gen_params)
    else:
        raise NotImplementedError(
            f"Generation method: {gen_method_type} not implemented!"
        )
    pipeline["save"](syn_df_proc, fn=f"{output_dir}/syn_df_proc")

    # Post-process synthetic data based on benchmark type and generation method
    # type to fit the original benchmark's pipeline
    log.info("Post-processing synthetic data...")
    syn_df, syn_df_tool_calls = pipeline["postprocess"](syn_df_proc)
    pipeline["save"](syn_df, fn=f"{output_dir}/syn_df")
    if syn_df_tool_calls is not None:
        pipeline["save"](syn_df_tool_calls, fn=f"{output_dir}/syn_df_tool_calls")

    log.info("Done!")


if __name__ == "__main__":
    main()
