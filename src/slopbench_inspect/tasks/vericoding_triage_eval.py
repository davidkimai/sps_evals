from __future__ import annotations

from inspect_ai import Task, task
from inspect_ai.model import GenerateConfig

from slopbench_inspect.datasets.vericoding import load_vericoding_samples
from slopbench_inspect.scorers.vericoding import (
    vericoding_runtime_log_scorer,
    vericoding_trust_boundary_scorer,
)
from slopbench_inspect.solvers.vericoding_runtime import vericoding_runtime_provenance_solver


@task
def vericoding_triage_eval(
    root: str = "runs/vericoding_research_v3",
    split: str = "confirmatory",
) -> Task:
    return Task(
        dataset=load_vericoding_samples(root, split=split, condition="triage_eval", source="primary_core"),
        solver=vericoding_runtime_provenance_solver("triage_eval"),
        scorer=[vericoding_runtime_log_scorer(), vericoding_trust_boundary_scorer()],
        config=GenerateConfig(max_tokens=256, temperature=0.0),
        name=f"vericoding_triage_eval_{split}",
        metadata=_metadata("triage_eval", split),
    )


def _metadata(surface: str, split: str) -> dict[str, object]:
    return {
        "schema": "specoracle.inspect_task.v3",
        "program_version": "vericoding_research_v3",
        "surface": surface,
        "split": split,
        "raw_content_committed": False,
    }
