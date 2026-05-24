from specoracle.vericoding.selectors.llm_judge_selector import select_with_llm_judge
from specoracle.vericoding.selectors.random_selector import select_random
from specoracle.vericoding.selectors.specoracle_selector import select_with_specoracle
from specoracle.vericoding.selectors.structural_selector import select_with_structural
from specoracle.vericoding.selectors.tests_only_selector import select_with_tests_only

SELECTORS = {
    "random_selector": select_random,
    "tests_only_selector": select_with_tests_only,
    "structural_selector": select_with_structural,
    "llm_judge_selector": select_with_llm_judge,
    "specoracle_selector": select_with_specoracle,
}

__all__ = [
    "SELECTORS",
    "select_random",
    "select_with_llm_judge",
    "select_with_specoracle",
    "select_with_structural",
    "select_with_tests_only",
]
