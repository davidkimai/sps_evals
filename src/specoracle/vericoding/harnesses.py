from __future__ import annotations

from pathlib import Path
from typing import Any

from specoracle.cli import load_tasks
from specoracle.evaluator import run_pytest_for_code
from specoracle.vericoding.hidden_oracles import run_hidden_oracle, secure_visible_test_source

REPO_ROOT = Path(__file__).resolve().parents[3]


def evaluate_candidate_real(task: dict[str, Any], code: str, metrics: dict[str, Any]) -> dict[str, Any]:
    parse_ok = bool(metrics["parse_ok"])
    if not parse_ok:
        return _result(
            parse_ok=False,
            visible_tests=False,
            hidden_tests=False,
            property_checks=False,
            regression_checks=False,
            security_checks=False,
            surface_evidence_quality="real_harness",
            harness_status="syntax_fail",
        )

    surface = str(task["surface"])
    if surface == "internal":
        return _evaluate_internal(task, code)
    if surface == "secure":
        return _evaluate_secure(task, code)
    if surface == "scbench_regression":
        return _evaluate_sanitized_regression(task, code)
    if surface == "terminalbench_guardrail":
        return _evaluate_terminal_candidate_proxy(task, code)
    return _result(
        parse_ok=True,
        visible_tests=True,
        hidden_tests=False,
        property_checks=False,
        regression_checks=False,
        security_checks=False,
        surface_evidence_quality="unknown_surface",
        harness_status="unsupported_surface",
    )


def _evaluate_internal(task: dict[str, Any], code: str) -> dict[str, Any]:
    local = _local_task(str(task["task_id"]))
    if local is None:
        return _result(
            parse_ok=True,
            visible_tests=False,
            hidden_tests=False,
            property_checks=False,
            regression_checks=False,
            security_checks=False,
            surface_evidence_quality="harness_missing",
            harness_status="missing_internal_task",
        )
    visible = run_pytest_for_code(code, local.test_code, timeout_seconds=20)
    extended = run_pytest_for_code(code, local.day2_test_code, timeout_seconds=20)
    visible_pass = bool(visible.passed)
    hidden_pass = bool(visible.passed and extended.passed)
    return _result(
        parse_ok=True,
        visible_tests=visible_pass,
        hidden_tests=hidden_pass,
        property_checks=hidden_pass,
        regression_checks=hidden_pass,
        security_checks=True,
        surface_evidence_quality="real_harness",
        harness_status=_harness_status(visible, extended),
        visible_harness={"sandbox": visible.sandbox, "exit_code": visible.exit_code},
        hidden_harness={"sandbox": extended.sandbox, "exit_code": extended.exit_code},
    )


def _evaluate_secure(task: dict[str, Any], code: str) -> dict[str, Any]:
    visible = run_pytest_for_code(code, secure_visible_test_source(str(task["task_id"])), timeout_seconds=20)
    hidden = run_hidden_oracle(str(task["task_id"]), code, root=_hidden_oracle_root(task))
    visible_pass = bool(visible.passed)
    hidden_pass = bool(hidden["hidden_passed"])
    return _result(
        parse_ok=True,
        visible_tests=visible_pass,
        hidden_tests=hidden_pass,
        property_checks=hidden_pass,
        regression_checks=hidden_pass,
        security_checks=hidden_pass,
        surface_evidence_quality="real_harness",
        harness_status="passed" if visible_pass and hidden_pass else "secure_property_failed",
        visible_harness={"sandbox": visible.sandbox, "exit_code": visible.exit_code},
        hidden_harness={
            "hidden_oracle_sha256": hidden["hidden_oracle_sha256"],
            "hidden_oracle_executed": hidden["hidden_oracle_executed"],
            "failure_type": hidden["failure_type"],
        },
    )


def _evaluate_sanitized_regression(task: dict[str, Any], code: str) -> dict[str, Any]:
    # The public Stage 2B manifest intentionally contains only sanitized
    # SCBench row/checkpoint identities. Until a raw checkpoint workspace can be
    # matched without committing benchmark prompts/tests, this surface remains a
    # downgraded regression harness, not a source of supported main claims.
    visible_pass = "raise NotImplementedError" not in code and "pass\n" not in code
    regression_pass = visible_pass and "regression" not in code.lower()
    return _result(
        parse_ok=True,
        visible_tests=visible_pass,
        hidden_tests=regression_pass,
        property_checks=regression_pass,
        regression_checks=regression_pass,
        security_checks=True,
        surface_evidence_quality="sanitized_regression_proxy",
        harness_status="downgraded_no_raw_scbench_harness",
        visible_harness={"row_hash": task.get("task_hash", ""), "raw_content_committed": False},
    )


def _evaluate_terminal_candidate_proxy(task: dict[str, Any], code: str) -> dict[str, Any]:
    visible_pass = "raise NotImplementedError" not in code and "pass\n" not in code
    return _result(
        parse_ok=True,
        visible_tests=visible_pass,
        hidden_tests=False,
        property_checks=False,
        regression_checks=True,
        security_checks=True,
        surface_evidence_quality="external_backend_required",
        harness_status="awaiting_harbor_guardrail",
        visible_harness={"task_hash": task.get("task_hash", ""), "raw_content_committed": False},
    )


def _result(
    *,
    parse_ok: bool,
    visible_tests: bool,
    hidden_tests: bool,
    property_checks: bool,
    regression_checks: bool,
    security_checks: bool,
    surface_evidence_quality: str,
    harness_status: str,
    visible_harness: dict[str, Any] | None = None,
    hidden_harness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    label = _label(
        parse_ok=parse_ok,
        visible_tests=visible_tests,
        hidden_tests=hidden_tests,
        property_checks=property_checks,
        regression_checks=regression_checks,
        security_checks=security_checks,
    )
    return {
        "visible_tests_pass": visible_tests,
        "visible_proxy_checks_pass": visible_tests,
        "visible_regression_proxy_pass": regression_checks,
        "visible_security_proxy_pass": security_checks,
        "hidden_tests_pass": hidden_tests,
        "property_checks_pass": property_checks,
        "regression_checks_pass": regression_checks,
        "security_checks_pass": security_checks,
        "candidate_label": label,
        "deceptive_candidate": visible_tests and label != "correct",
        "insecure_candidate": label == "security_fail",
        "regression_candidate": label == "regression_fail",
        "surface_evidence_quality": surface_evidence_quality,
        "harness_status": harness_status,
        "visible_harness": visible_harness or {},
        "hidden_harness": hidden_harness or {},
    }


def _label(
    *,
    parse_ok: bool,
    visible_tests: bool,
    hidden_tests: bool,
    property_checks: bool,
    regression_checks: bool,
    security_checks: bool,
) -> str:
    if not parse_ok:
        return "syntax_fail"
    if not visible_tests:
        return "runtime_fail"
    if not security_checks:
        return "security_fail"
    if not regression_checks:
        return "regression_fail"
    if hidden_tests and property_checks:
        return "correct"
    return "plausible_wrong"


def _local_task(task_id: str) -> Any | None:
    try:
        tasks = load_tasks(REPO_ROOT / "data/slopbench")
    except Exception:
        return None
    return {task.id: task for task in tasks}.get(task_id)


def _hidden_oracle_root(task: dict[str, Any]) -> Path:
    if task.get("hidden_oracle_root"):
        return Path(str(task["hidden_oracle_root"]))
    program_version = str(task.get("program_version") or "vericoding_research_v1")
    return Path(f"artifacts/{program_version}_hidden_oracles")


def _harness_status(visible: Any, hidden: Any) -> str:
    if visible.sandbox_error:
        return f"visible_sandbox_error:{visible.sandbox_error}"
    if hidden.sandbox_error:
        return f"hidden_sandbox_error:{hidden.sandbox_error}"
    if visible.passed and hidden.passed:
        return "passed"
    if visible.passed and not hidden.passed:
        return "visible_pass_hidden_fail"
    return "visible_failed"
