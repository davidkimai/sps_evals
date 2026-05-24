from __future__ import annotations

from inspect_ai import Task, task
from inspect_ai.model import GenerateConfig
from inspect_ai.solver import Solver

from slopbench_inspect.datasets.slopbench import load_slopbench_samples
from slopbench_inspect.scorers.structural import pytest_scorer, structural_scorer
from slopbench_inspect.solvers.baseline import baseline_solver
from slopbench_inspect.solvers.hybrid import hybrid_solver
from slopbench_inspect.solvers.karpathy import karpathy_solver
from slopbench_inspect.solvers.reference import reference_solution_solver


@task
def slopbench_internal_smoke(
    dataset_dir: str = "data/slopbench_min",
    task_ids: str = "nested_json_index",
    variant: str = "reference",
    max_cc: float = 8.0,
    max_nesting: int = 3,
    hybrid_max_retries: int = 3,
) -> Task:
    """Small Inspect-native SlopBench task for runtime and parity smoke tests."""
    selected_ids = [item.strip() for item in task_ids.split(",") if item.strip()]
    return Task(
        dataset=load_slopbench_samples(dataset_dir, task_ids=selected_ids),
        solver=_solver_for_variant(
            variant,
            max_cc=max_cc,
            max_nesting=max_nesting,
            hybrid_max_retries=hybrid_max_retries,
        ),
        scorer=[structural_scorer(), pytest_scorer()],
        config=GenerateConfig(max_tokens=4096, temperature=0.2),
        name=f"slopbench_internal_{variant}",
        metadata={
            "schema": "specoracle.inspect_task.v1",
            "benchmark": "slopbench",
            "variant": variant,
            "purpose": "internal Inspect-native smoke/parity task",
        },
    )


def _solver_for_variant(
    variant: str,
    *,
    max_cc: float,
    max_nesting: int,
    hybrid_max_retries: int,
) -> Solver | list[Solver]:
    if variant == "reference":
        return reference_solution_solver()
    if variant == "baseline":
        return baseline_solver()
    if variant == "hybrid":
        return hybrid_solver(
            max_cc=max_cc,
            max_nesting=max_nesting,
            max_retries=hybrid_max_retries,
        )
    if variant == "karpathy":
        return karpathy_solver()
    raise ValueError(f"unknown Inspect SlopBench variant: {variant}")
