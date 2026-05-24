from __future__ import annotations

from inspect_ai import Task, task
from inspect_ai.model import GenerateConfig

from slopbench_inspect.datasets.scbench import load_scbench_manifest_samples
from slopbench_inspect.scorers.structural import structural_scorer
from slopbench_inspect.solvers.baseline import baseline_solver
from slopbench_inspect.solvers.hybrid import hybrid_solver
from slopbench_inspect.solvers.karpathy import karpathy_solver
from slopbench_inspect.solvers.reference import reference_solution_solver


@task
def scbench_external_subset(
    manifest_path: str = "runs/sprint9_external_subset_manifest.json",
    variant: str = "reference",
    max_cc: float = 8.0,
    max_nesting: int = 3,
    hybrid_max_retries: int = 3,
) -> Task:
    """Sanitized Inspect task surface for the pinned Sprint 9 external subset.

    This task intentionally loads only the public manifest. Raw benchmark
    prompts/tests are not embedded in committed task fixtures or tracked logs.
    Paid/raw execution should be routed through ignored runtime logs and the
    wrapper path documented in ``integrations/inspect/USAGE.md``.
    """
    if variant == "reference":
        solver = reference_solution_solver()
    elif variant == "baseline":
        solver = baseline_solver()
    elif variant == "hybrid":
        solver = hybrid_solver(
            max_cc=max_cc,
            max_nesting=max_nesting,
            max_retries=hybrid_max_retries,
        )
    elif variant == "karpathy":
        solver = karpathy_solver()
    else:
        raise ValueError(f"unknown SCBench Inspect variant: {variant}")

    return Task(
        dataset=load_scbench_manifest_samples(manifest_path),
        solver=solver,
        scorer=[structural_scorer()],
        config=GenerateConfig(max_tokens=12000, temperature=0.8),
        name=f"sprint9_scbench_subset_{variant}",
        metadata={
            "schema": "specoracle.inspect_task.v1",
            "benchmark": "scbench",
            "variant": variant,
            "purpose": "sanitized external subset task surface",
            "representativeness": "diagnostic_subset_not_population_estimate",
        },
    )
