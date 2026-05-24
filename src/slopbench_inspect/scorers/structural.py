from __future__ import annotations

from typing import Any

from inspect_ai.scorer import CORRECT, INCORRECT, Score, Target, accuracy, scorer
from inspect_ai.solver import TaskState

from specoracle.generator import extract_python_code
from specoracle.metrics import build_structural_metric_record

from slopbench_inspect.sandboxing.docker_pytest import (
    pytest_result_metadata,
    run_sandboxed_pytest,
)


def extract_completion_code(text: str) -> str:
    """Extract Python source from a model completion."""
    return extract_python_code(text)


def score_structural_code(code: str, *, reference_code: str | None = None) -> dict[str, Any]:
    """Compute the shared SpecOracle structural metric record for Python code."""
    return build_structural_metric_record(code, language="python", reference_code=reference_code)


@scorer(metrics=[])
def structural_scorer() -> Any:
    async def score(state: TaskState, target: Target) -> Score:
        code = extract_completion_code(state.output.completion if state.output else "")
        metrics = score_structural_code(
            code,
            reference_code=state.metadata.get("human_reference") if state.metadata else None,
        )
        return Score(
            value={
                "parse_ok": bool(metrics["parse_ok"]),
                "cc_average": _number_or_zero(metrics.get("cc_average")),
                "max_nesting_depth": _number_or_zero(metrics.get("max_nesting_depth")),
                "maintainability_index": _number_or_zero(metrics.get("maintainability_index")),
                "redundancy_score": _number_or_zero(metrics.get("redundancy_score")),
            },
            answer=code[:200],
            metadata=metrics,
        )

    return score


@scorer(metrics=[accuracy()])
def pytest_scorer(*, timeout_seconds: float = 20.0) -> Any:
    async def score(state: TaskState, target: Target) -> Score:
        metadata = state.metadata or {}
        test_code = metadata.get("test_code")
        if not test_code:
            return Score(
                value=INCORRECT,
                explanation="missing pytest test_code metadata",
                metadata={"failure_type": "missing_test_code"},
            )
        code = extract_completion_code(state.output.completion if state.output else "")
        result = run_sandboxed_pytest(code, test_code, timeout_seconds=timeout_seconds)
        return Score(
            value=CORRECT if result.passed else INCORRECT,
            explanation=result.failure_type,
            metadata=pytest_result_metadata(result),
        )

    return score


def _number_or_zero(value: Any) -> float:
    return float(value) if isinstance(value, int | float) else 0.0
