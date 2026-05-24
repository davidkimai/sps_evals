from __future__ import annotations

from inspect_ai import Task, task
from inspect_ai.model import GenerateConfig

from slopbench_inspect.datasets.terminalbench import load_terminalbench_python_slice_samples
from slopbench_inspect.scorers.structural import structural_scorer
from slopbench_inspect.solvers.reference import reference_solution_solver


@task
def terminalbench_python_slice(
    closeout_root: str = "runs/sprint10_closeout_v1",
    slice_name: str = "dev",
    condition: str = "baseline",
) -> Task:
    """Sanitized Inspect task surface for the Sprint 10 Terminal-Bench slice.

    Harbor remains the raw execution backend. This task provides stable sample
    identity, condition metadata, and result-summary alignment in Inspect.
    """
    return Task(
        dataset=load_terminalbench_python_slice_samples(
            closeout_root,
            slice_name=slice_name,
            condition=condition,
        ),
        solver=reference_solution_solver(),
        scorer=[structural_scorer()],
        config=GenerateConfig(max_tokens=2048, temperature=0.0),
        name=f"terminalbench_{slice_name}_{condition}",
        metadata={
            "schema": "specoracle.inspect_task.v1",
            "benchmark": "terminalbench",
            "slice": slice_name,
            "condition": condition,
            "execution_backend": "harbor",
            "control_plane": "inspect",
            "representativeness": "pinned_python_slice_not_population_estimate",
            "raw_content_committed": False,
        },
    )
