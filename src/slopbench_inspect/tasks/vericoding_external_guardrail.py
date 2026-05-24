from __future__ import annotations

from inspect_ai import Task, task
from inspect_ai.model import GenerateConfig

from slopbench_inspect.datasets.vericoding import load_vericoding_samples
from slopbench_inspect.scorers.vericoding import vericoding_summary_scorer
from slopbench_inspect.solvers.reference import reference_solution_solver


@task
def vericoding_external_guardrail(
    root: str = "runs/vericoding_research_v3",
    split: str = "confirmatory",
) -> Task:
    return Task(
        dataset=load_vericoding_samples(
            root,
            surface="terminalbench_guardrail",
            split=split,
            condition="external_guardrail",
            source="external_guardrail",
        ),
        solver=reference_solution_solver(),
        scorer=[vericoding_summary_scorer()],
        config=GenerateConfig(max_tokens=1024, temperature=0.0),
        name=f"vericoding_external_guardrail_{split}",
        metadata={
            "schema": "specoracle.inspect_task.v1",
            "program_version": "vericoding_research_v3",
            "surface": "terminalbench_guardrail",
            "split": split,
            "raw_content_committed": False,
        },
    )
