from __future__ import annotations

from inspect_ai import Task, task
from inspect_ai.model import GenerateConfig

from slopbench_inspect.datasets.vericoding import load_vericoding_samples
from slopbench_inspect.scorers.vericoding import (
    vericoding_candidate_support_scorer,
    vericoding_hidden_disagreement_scorer,
    vericoding_runtime_log_scorer,
)
from slopbench_inspect.solvers.reference import reference_solution_solver


@task
def vericoding_internal_basins(
    root: str = "runs/vericoding_research_v3",
    split: str = "confirmatory",
) -> Task:
    return Task(
        dataset=load_vericoding_samples(
            root,
            surface="internal",
            split=split,
            condition="internal_basins",
            source="internal_regression",
        ),
        solver=reference_solution_solver(),
        scorer=[
            vericoding_runtime_log_scorer(),
            vericoding_candidate_support_scorer(),
            vericoding_hidden_disagreement_scorer(),
        ],
        config=GenerateConfig(max_tokens=1024, temperature=0.0),
        name=f"vericoding_internal_basins_{split}",
        metadata={
            "schema": "specoracle.inspect_task.v3",
            "program_version": "vericoding_research_v3",
            "surface": "internal",
            "split": split,
            "raw_content_committed": False,
        },
    )
