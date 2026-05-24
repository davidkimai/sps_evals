from __future__ import annotations

from inspect_ai import Task, task
from inspect_ai.model import GenerateConfig

from slopbench_inspect.datasets.vericoding import load_vericoding_samples
from slopbench_inspect.scorers.vericoding import (
    vericoding_runtime_log_scorer,
    vericoding_trust_boundary_scorer,
)
from slopbench_inspect.solvers.reference import reference_solution_solver


@task
def vericoding_trust_boundary_review(
    root: str = "runs/vericoding_research_v3",
    split: str = "confirmatory",
) -> Task:
    return Task(
        dataset=load_vericoding_samples(
            root,
            split=split,
            condition="trust_boundary_review",
            source="primary_core",
        ),
        solver=reference_solution_solver(),
        scorer=[
            vericoding_trust_boundary_scorer(),
            vericoding_runtime_log_scorer(),
        ],
        config=GenerateConfig(max_tokens=1024, temperature=0.0),
        name=f"vericoding_trust_boundary_review_{split}",
        metadata={
            "schema": "specoracle.inspect_task.v3",
            "program_version": "vericoding_research_v3",
            "surface": "primary_core",
            "split": split,
            "raw_content_committed": False,
        },
    )
