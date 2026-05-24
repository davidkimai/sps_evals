from __future__ import annotations

from inspect_ai import Task, task
from inspect_ai.model import GenerateConfig

from slopbench_inspect.datasets.vericoding import load_vericoding_samples
from slopbench_inspect.scorers.vericoding import vericoding_summary_scorer
from slopbench_inspect.solvers.reference import reference_solution_solver


@task
def vericoding_candidate_bank(
    root: str = "runs/vericoding_research_v3",
    split: str = "dev",
) -> Task:
    return Task(
        dataset=load_vericoding_samples(root, split=split, condition="candidate_bank"),
        solver=reference_solution_solver(),
        scorer=[vericoding_summary_scorer()],
        config=GenerateConfig(max_tokens=1024, temperature=0.0),
        name=f"vericoding_candidate_bank_{split}",
        metadata=_metadata("candidate_bank", split),
    )


def _metadata(surface: str, split: str) -> dict[str, object]:
    return {
        "schema": "specoracle.inspect_task.v1",
        "program_version": "vericoding_research_v3",
        "surface": surface,
        "split": split,
        "raw_content_committed": False,
    }
