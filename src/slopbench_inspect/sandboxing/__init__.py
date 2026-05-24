"""Sandbox wrappers used by Inspect-native scorers."""

from slopbench_inspect.sandboxing.docker_pytest import (
    InspectPytestResult,
    run_sandboxed_pytest,
    sanitize_pytest_result,
)

__all__ = ["InspectPytestResult", "run_sandboxed_pytest", "sanitize_pytest_result"]
