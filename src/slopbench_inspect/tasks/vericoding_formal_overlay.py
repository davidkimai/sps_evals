from __future__ import annotations

from inspect_ai import Task, task
from inspect_ai.model import GenerateConfig

from slopbench_inspect.datasets.vericoding import load_vericoding_samples
from slopbench_inspect.scorers.vericoding import vericoding_runtime_log_scorer
from slopbench_inspect.solvers.reference import reference_solution_solver


@task
def vericoding_formal_overlay(
    root: str = "runs/vericoding_research_v3",
    split: str = "confirmatory",
) -> Task:
    return Task(
        dataset=load_vericoding_samples(
            root,
            split=split,
            condition="formal_overlay",
            source="formal_overlay",
        ),
        solver=reference_solution_solver(),
        scorer=[vericoding_runtime_log_scorer()],
        config=GenerateConfig(max_tokens=1024, temperature=0.0),
        name=f"vericoding_formal_overlay_{split}",
        metadata={
            "schema": "specoracle.inspect_task.v3",
            "program_version": "vericoding_research_v3",
            "surface": "formal_overlay",
            "split": split,
            "raw_content_committed": False,
        },
    )
