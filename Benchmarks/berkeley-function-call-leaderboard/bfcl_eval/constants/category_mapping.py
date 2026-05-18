VERSION_PREFIX = "BFCL_v4"


ALL_AVAILABLE_MEMORY_BACKENDS = [
    "kv",
    "vector",
    "rec_sum",
]

NON_LIVE_CATEGORY = [
    "simple_python",
    "simple_java",
    "simple_javascript",
    "multiple",
    "parallel",
    "parallel_multiple",
    "irrelevance",
    # "exec_simple",
    # "exec_parallel",
    # "exec_multiple",
    # "exec_parallel_multiple",
    # "rest",
    # "sql",
    # "chatable",
]
LIVE_CATEGORY = [
    "live_simple",
    "live_multiple",
    "live_parallel",
    "live_parallel_multiple",
    "live_irrelevance",
    "live_relevance",
]
MULTI_TURN_CATEGORY = [
    "multi_turn_base",
    "multi_turn_miss_func",
    "multi_turn_miss_param",
    "multi_turn_long_context",
    # "multi_turn_composite",
    "oversample_frac0_1",
    "oversample_frac0_3",
    "oversample_frac0_5",
    "oversample_frac0_7",
    "oversample_frac0_9",
    "oversample_frac0",
    "oversample_frac1",
    "fewshot_fixed_ex0",
    "fewshot_fixed_ex1",
    "fewshot_fixed_ex3",
    "fewshot_fixed_ex5",
    "fewshot_rand_ex0",
    "fewshot_rand_ex1",
    "fewshot_rand_ex3",
    "fewshot_rand_ex5",
    "blankfill_prob0_1",
    "blankfill_prob0_3",
    "blankfill_prob0_5",
    "blankfill_prob0_7",
    "blankfill_prob0_9",
    "dropmin_0secondary_api_frac0_3",
    "dropmin_1secondary_api_frac0_3",
    "dropmin_2secondary_api_frac0_3",
    "dropmin_3secondary_api_frac0_3",
    "invalidate_frac0",
    "invalidate_frac0_1",
    "invalidate_frac0_2",
    "invalidate_frac0_3",
    "invalidate_frac0_4",
    "invalidate_frac0_5",
    "invalidate_frac0_6",
    "invalidate_frac0_7",
    "invalidate_frac0_8",
    "invalidate_frac0_9",
    "invalidate_frac1"
]
WEB_SEARCH_CATEGORY = [
    "web_search_base",
    "web_search_no_snippet",
]

MEMORY_CATEGORY = [f"memory_{backend}" for backend in ALL_AVAILABLE_MEMORY_BACKENDS]
MEMORY_SCENARIO_NAME = [
    "student",
    "customer",
    "finance",
    "healthcare",
    "notetaker",
]


SINGLE_TURN_CATEGORY = NON_LIVE_CATEGORY + LIVE_CATEGORY
AGENTIC_CATEGORY = MEMORY_CATEGORY + WEB_SEARCH_CATEGORY
NON_SCORING_CATEGORY = ["format_sensitivity"]

ALL_SCORING_CATEGORIES = SINGLE_TURN_CATEGORY + MULTI_TURN_CATEGORY + AGENTIC_CATEGORY
ALL_CATEGORIES = ALL_SCORING_CATEGORIES + NON_SCORING_CATEGORY

TEST_COLLECTION_MAPPING = {
    "all": ALL_CATEGORIES,
    "all_scoring": ALL_SCORING_CATEGORIES,
    "multi_turn": MULTI_TURN_CATEGORY,
    "single_turn": SINGLE_TURN_CATEGORY,
    "live": LIVE_CATEGORY,
    "non_live": NON_LIVE_CATEGORY,
    "non_python": [
        "simple_java",
        "simple_javascript",
    ],
    "python": [
        "simple_python",
        "irrelevance",
        "parallel",
        "multiple",
        "parallel_multiple",
        "live_simple",
        "live_multiple",
        "live_parallel",
        "live_parallel_multiple",
        "live_irrelevance",
        "live_relevance",
    ],
    "memory": MEMORY_CATEGORY,
    "web_search": WEB_SEARCH_CATEGORY,
    "agentic": AGENTIC_CATEGORY,
}
