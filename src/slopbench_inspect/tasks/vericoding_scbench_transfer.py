from __future__ import annotations

from inspect_ai import Task, task
from inspect_ai.model import GenerateConfig

from slopbench_inspect.datasets.vericoding import load_vericoding_samples
from slopbench_inspect.scorers.vericoding import (
    vericoding_hidden_disagreement_scorer,
    vericoding_runtime_log_scorer,
)
from slopbench_inspect.solvers.reference import reference_solution_solver


@task
def vericoding_scbench_transfer(
    root: str = "runs/vericoding_research_v3",
    split: str = "confirmatory",
) -> Task:
    return Task(
        dataset=load_vericoding_samples(
            root,
            surface="scbench_regression",
            split=split,
            condition="scbench_transfer",
            source="scbench_transfer",
        ),
        solver=reference_solution_solver(),
        scorer=[
            vericoding_runtime_log_scorer(),
            vericoding_hidden_disagreement_scorer(),
        ],
        config=GenerateConfig(max_tokens=1024, temperature=0.0),
        name=f"vericoding_scbench_transfer_{split}",
        metadata={
            "schema": "specoracle.inspect_task.v3",
            "program_version": "vericoding_research_v3",
            "surface": "scbench_regression",
            "split": split,
            "raw_content_committed": False,
        },
    )
