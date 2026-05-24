from __future__ import annotations

from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.dataset import MemoryDataset
from inspect_ai.model import GenerateConfig
from inspect_ai.scorer import CORRECT, INCORRECT, Score, Target, accuracy, scorer
from slopbench_inspect.solvers.reference import reference_solution_solver
from specoracle.vericoding.formal_specs import FORMAL_DEFAULT_ROOT, FORMAL_PROGRAM_VERSION


@scorer(metrics=[accuracy()])
def formal_validation_report_scorer():
    async def score(state, target: Target) -> Score:
        root = Path(str(state.metadata.get("root") or FORMAL_DEFAULT_ROOT.as_posix()))
        ok = (root / "reports" / "formal_evaluator_validation.md").exists()
        return Score(value=CORRECT if ok else INCORRECT, explanation="formal validation report present" if ok else "missing formal validation report")
    return score


@task
def vericoding_formal_validation(root: str = FORMAL_DEFAULT_ROOT.as_posix(), split: str = "dev") -> Task:
    dataset = MemoryDataset(
        samples=[
            Sample(
                id="formal-validation",
                input="Formal evaluator validation status.",
                target="",
                metadata={"root": root, "split": split, "program_version": FORMAL_PROGRAM_VERSION},
            )
        ],
        name="formal_validation",
    )
    return Task(
        dataset=dataset,
        solver=reference_solution_solver(),
        scorer=[formal_validation_report_scorer()],
        config=GenerateConfig(max_tokens=128, temperature=0.0),
        name="vericoding_formal_validation",
        metadata={
            "schema": "specoracle.inspect_task.formal.v1",
            "program_version": FORMAL_PROGRAM_VERSION,
            "surface": "formal_validation",
            "split": split,
            "raw_content_committed": False,
        },
    )
