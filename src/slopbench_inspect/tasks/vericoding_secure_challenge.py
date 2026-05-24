from __future__ import annotations

from inspect_ai import Task, task
from inspect_ai.model import GenerateConfig

from slopbench_inspect.datasets.vericoding import load_vericoding_samples
from slopbench_inspect.scorers.vericoding import (
    vericoding_candidate_support_scorer,
    vericoding_runtime_log_scorer,
    vericoding_secure_false_accept_scorer,
)
from slopbench_inspect.solvers.reference import reference_solution_solver


@task
def vericoding_secure_challenge(
    root: str = "runs/vericoding_research_v3",
    split: str = "confirmatory",
) -> Task:
    return Task(
        dataset=load_vericoding_samples(
            root,
            surface="secure",
            split=split,
            condition="secure_challenge",
            source="secure_challenge",
        ),
        solver=reference_solution_solver(),
        scorer=[
            vericoding_runtime_log_scorer(),
            vericoding_candidate_support_scorer(),
            vericoding_secure_false_accept_scorer(),
        ],
        config=GenerateConfig(max_tokens=1024, temperature=0.0),
        name=f"vericoding_secure_challenge_{split}",
        metadata={
            "schema": "specoracle.inspect_task.v3",
            "program_version": "vericoding_research_v3",
            "surface": "secure",
            "split": split,
            "raw_content_committed": False,
        },
    )
