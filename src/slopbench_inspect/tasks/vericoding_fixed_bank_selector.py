from __future__ import annotations

from inspect_ai import Task, task
from inspect_ai.model import GenerateConfig

from slopbench_inspect.datasets.vericoding import load_vericoding_samples
from slopbench_inspect.scorers.vericoding import (
    vericoding_hidden_disagreement_scorer,
    vericoding_runtime_log_scorer,
)
from slopbench_inspect.solvers.vericoding_runtime import vericoding_runtime_provenance_solver


@task
def vericoding_fixed_bank_selector(
    root: str = "runs/vericoding_research_v3",
    split: str = "confirmatory",
) -> Task:
    return Task(
        dataset=load_vericoding_samples(root, split=split, condition="fixed_bank_selector", source="primary_core"),
        solver=vericoding_runtime_provenance_solver("fixed_bank_selector"),
        scorer=[vericoding_runtime_log_scorer(), vericoding_hidden_disagreement_scorer()],
        config=GenerateConfig(max_tokens=256, temperature=0.0),
        name=f"vericoding_fixed_bank_selector_{split}",
        metadata=_metadata("fixed_bank_selector", split),
    )


def _metadata(surface: str, split: str) -> dict[str, object]:
    return {
        "schema": "specoracle.inspect_task.v3",
        "program_version": "vericoding_research_v3",
        "surface": surface,
        "split": split,
        "raw_content_committed": False,
    }
