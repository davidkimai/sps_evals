from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from specoracle.evaluator import PytestResult, run_pytest_for_code, run_pytest_for_files


@dataclass(frozen=True)
class InspectPytestResult:
    passed: bool
    exit_code: int
    timed_out: bool
    sandbox_error: str | None
    failure_type: str
    stdout_chars: int
    stderr_chars: int
    duration_seconds: float


def run_sandboxed_pytest(
    code: str,
    test_code: str | dict[str, str],
    *,
    timeout_seconds: float = 20.0,
) -> InspectPytestResult:
    """Run generated Python against pytest and return sanitized metadata only."""
    if isinstance(test_code, dict):
        result = run_pytest_for_files(code, test_code, timeout_seconds=timeout_seconds)
    else:
        result = run_pytest_for_code(code, test_code, timeout_seconds=timeout_seconds)
    return sanitize_pytest_result(result)


def sanitize_pytest_result(result: PytestResult) -> InspectPytestResult:
    return InspectPytestResult(
        passed=result.passed,
        exit_code=result.exit_code,
        timed_out=result.timed_out,
        sandbox_error=result.sandbox_error,
        failure_type=_failure_type(result),
        stdout_chars=len(result.stdout or ""),
        stderr_chars=len(result.stderr or ""),
        duration_seconds=result.duration_seconds,
    )


def pytest_result_metadata(result: InspectPytestResult) -> dict[str, Any]:
    return {
        "pytest_passed": result.passed,
        "pytest_exit_code": result.exit_code,
        "pytest_timed_out": result.timed_out,
        "pytest_sandbox_error": bool(result.sandbox_error),
        "failure_type": result.failure_type,
        "stdout_chars": result.stdout_chars,
        "stderr_chars": result.stderr_chars,
        "duration_seconds": result.duration_seconds,
    }


def _failure_type(result: PytestResult) -> str:
    if result.passed:
        return "passed"
    if result.sandbox_error:
        return "sandbox_error"
    if result.timed_out or result.exit_code == 124:
        return "timeout"
    combined = f"{result.stdout}\n{result.stderr}".lower()
    if "syntaxerror" in combined or "indentationerror" in combined:
        return "syntax_error"
    if "modulenotfounderror" in combined or "importerror" in combined or "attributeerror" in combined:
        return "runtime_error"
    if "assert" in combined or "failed" in combined:
        return "assertion_failure"
    return "runtime_error"
