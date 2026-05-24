from __future__ import annotations

from inspect_ai import Task, task
from inspect_ai.model import GenerateConfig

from slopbench_inspect.datasets.vericoding_formal_eval import load_formal_eval_samples
from specoracle.vericoding.formal_specs import FORMAL_DEFAULT_ROOT, FORMAL_PROGRAM_VERSION
from slopbench_inspect.scorers.vericoding import (
    vericoding_candidate_support_scorer,
    vericoding_hidden_disagreement_scorer,
    vericoding_runtime_log_scorer,
    vericoding_trust_boundary_scorer,
)
from slopbench_inspect.solvers.reference import reference_solution_solver


@task
def vericoding_formal_confirmatory(root: str = FORMAL_DEFAULT_ROOT.as_posix(), split: str = "confirmatory") -> Task:
    return Task(
        dataset=load_formal_eval_samples(root, split=split, phase="confirmatory"),
        solver=reference_solution_solver(),
        scorer=[
            vericoding_runtime_log_scorer(),
            vericoding_candidate_support_scorer(),
            vericoding_hidden_disagreement_scorer(),
            vericoding_trust_boundary_scorer(),
        ],
        config=GenerateConfig(max_tokens=256, temperature=0.0),
        name=f"vericoding_formal_confirmatory_{split}",
        metadata={
            "schema": "specoracle.inspect_task.formal.v1",
            "program_version": FORMAL_PROGRAM_VERSION,
            "surface": "formal_confirmatory",
            "split": split,
            "raw_content_committed": False,
        },
    )
