from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from subprocess import run
from typing import Any

from specoracle.vericoding.formal_specs import FORMAL_PROGRAM_VERSION, FORMAL_PUBLIC_SPEC_PATH, formal_specs_by_id, visible_test_source
from specoracle.vericoding.schemas import file_sha256, stable_hash

REPO_ROOT = Path(__file__).resolve().parents[3]
LEAN_ROOT = REPO_ROOT / "formal" / "lean" / "vericoding_formal_eval_v1"
ELAN_LAKE = Path.home() / ".elan" / "bin" / "lake"
FORMAL_CASE_EXPORT = REPO_ROOT / "artifacts" / FORMAL_PROGRAM_VERSION / "formal_cases.json"


def export_formal_cases(output_path: Path = FORMAL_CASE_EXPORT) -> dict[str, list[dict[str, Any]]]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [str(ELAN_LAKE), "exe", "formal-export"]
    completed = run(
        command,
        cwd=LEAN_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "formal case export failed\n"
            f"stdout={completed.stdout[-2000:]}\n"
            f"stderr={completed.stderr[-2000:]}"
        )
    output_path.write_text(completed.stdout, encoding="utf-8")
    payload = json.loads(completed.stdout)
    by_task: dict[str, list[dict[str, Any]]] = {}
    for row in payload:
        by_task.setdefault(str(row["task_id"]), []).append(dict(row))
    return by_task


def load_exported_formal_cases(path: Path = FORMAL_CASE_EXPORT) -> dict[str, list[dict[str, Any]]]:
    if not path.exists():
        return export_formal_cases(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    by_task: dict[str, list[dict[str, Any]]] = {}
    for row in payload:
        by_task.setdefault(str(row["task_id"]), []).append(dict(row))
    return by_task


def evaluate_candidate_formal(
    task_id: str,
    code: str,
    *,
    formal_cases: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    specs = formal_specs_by_id(FORMAL_PUBLIC_SPEC_PATH)
    spec = specs[task_id]
    visible = _run_visible_pytest(code, visible_test_source(task_id), timeout_seconds=20)
    case_bank = formal_cases or load_exported_formal_cases()
    cases = case_bank.get(task_id, [])
    formal = _run_formal_cases(task_id, code, cases)
    review = _review_boundary(spec, code, formal_pass=bool(formal["formal_pass"]))
    secure_task = str(spec["surface"]) == "secure"
    formal_pass = bool(formal["formal_pass"])
    return {
        "task_id": task_id,
        "surface": spec["surface"],
        "visible_tests_pass": bool(visible["passed"]),
        "visible_compile_pass": bool(visible["parse_ok"]),
        "visible_proxy_checks_pass": bool(visible["passed"]),
        "visible_regression_proxy_pass": bool(visible["passed"]),
        "visible_security_proxy_pass": bool(visible["passed"]),
        "formal_pass": formal_pass,
        "hidden_tests_pass": formal_pass,
        "property_checks_pass": formal_pass,
        "regression_checks_pass": formal_pass,
        "security_checks_pass": formal_pass if secure_task else True,
        "candidate_label": _candidate_label(visible_pass=bool(visible["passed"]), formal_pass=formal_pass, secure_task=secure_task),
        "deceptive_candidate": bool(visible["passed"]) and not formal_pass,
        "insecure_candidate": secure_task and bool(visible["passed"]) and not formal_pass,
        "regression_candidate": (not secure_task) and bool(visible["passed"]) and not formal_pass,
        "surface_evidence_quality": "lean_backed_formal_cases",
        "harness_status": _harness_status(visible_pass=bool(visible["passed"]), formal_pass=formal_pass, review=review),
        "visible_harness": {"sandbox": visible["sandbox"], "exit_code": visible["exit_code"], "stderr": visible["stderr"][:400]},
        "hidden_harness": {
            "formal_case_count": len(cases),
            "formal_case_failures": formal["failure_count"],
            "first_failure_case_id": formal.get("first_failure_case_id") or "",
            "formal_case_export_sha256": file_sha256(FORMAL_CASE_EXPORT) if FORMAL_CASE_EXPORT.exists() else "",
        },
        "formal_case_results": formal,
        "review_boundary": review,
    }


def _run_visible_pytest(code: str, test_source: str, *, timeout_seconds: int) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="formal_visible_") as temp_dir:
        work = Path(temp_dir)
        solution_path = work / "solution.py"
        test_path = work / "test_visible.py"
        solution_path.write_text(code, encoding="utf-8")
        test_path.write_text(test_source, encoding="utf-8")
        completed = subprocess.run(
            ["python3", "-m", "pytest", "-q", "test_visible.py"],
            cwd=work,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        return {
            "passed": completed.returncode == 0,
            "exit_code": completed.returncode,
            "stdout": completed.stdout or "",
            "stderr": completed.stderr or "",
            "parse_ok": "SyntaxError" not in (completed.stderr or "") and "SyntaxError" not in (completed.stdout or ""),
            "sandbox": "local_pytest",
        }


def _run_formal_cases(task_id: str, code: str, cases: list[dict[str, Any]]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"formal_eval_{task_id}_") as temp_dir:
        work = Path(temp_dir)
        solution_path = work / "solution.py"
        solution_path.write_text(code, encoding="utf-8")
        try:
            module = _load_solution_module(solution_path)
        except Exception as exc:  # noqa: BLE001
            first_case_id = str(cases[0]["case_id"]) if cases else "module_load"
            failures = [{
                "case_id": first_case_id,
                "actual_exception": exc.__class__.__name__,
                "actual_message": str(exc),
            }]
            return {
                "formal_pass": False,
                "failure_count": len(failures),
                "first_failure_case_id": first_case_id,
                "failures": failures,
                "case_count": len(cases),
                "formal_case_ids": [str(row["case_id"]) for row in cases],
                "formal_case_bank_hash": stable_hash(cases),
            }
        failures: list[dict[str, Any]] = []
        for row in cases:
            ok, detail = _run_single_case(module, task_id, row)
            if not ok:
                failures.append({"case_id": row["case_id"], **detail})
        return {
            "formal_pass": not failures,
            "failure_count": len(failures),
            "first_failure_case_id": failures[0]["case_id"] if failures else "",
            "failures": failures,
            "case_count": len(cases),
            "formal_case_ids": [str(row["case_id"]) for row in cases],
            "formal_case_bank_hash": stable_hash(cases),
        }


def _load_solution_module(solution_path: Path) -> Any:
    module_name = f"solution_{solution_path.parent.name}"
    spec = importlib.util.spec_from_file_location(module_name, solution_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load solution module from {solution_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
        return module
    finally:
        sys.modules.pop(module_name, None)


def _run_single_case(module: Any, task_id: str, row: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    invocation = dict(row.get("invocation") or {})
    expected = row.get("expected")
    try:
        actual = _dispatch_call(module, task_id, invocation)
    except Exception as exc:  # noqa: BLE001
        if isinstance(expected, dict) and expected.get("raises") == exc.__class__.__name__:
            return True, {"expected": expected, "actual_exception": exc.__class__.__name__}
        return False, {
            "expected": expected,
            "actual_exception": exc.__class__.__name__,
            "actual_message": str(exc),
        }
    normalized = _normalize_actual(task_id, actual)
    if normalized == expected:
        return True, {"expected": expected, "actual": normalized}
    return False, {"expected": expected, "actual": normalized}


def _dispatch_call(module: Any, task_id: str, invocation: dict[str, Any]) -> Any:
    if task_id == "permission_gate":
        matrix = {
            role: {perm for perm, granted in perms.items() if granted}
            for role, perms in (invocation.get("matrix") or {}).items()
        }
        return module.has_permission(matrix, invocation["role"], invocation["permission"])
    if task_id == "feature_flag_matrix":
        defaults = dict(invocation["defaults"])
        segments = {name: dict(values) for name, values in (invocation["segments"] or {}).items()}
        user = dict(invocation["user"])
        if invocation["call"] == "resolve_flags":
            return module.resolve_flags(defaults, segments, user)
        return module.explain_flags(defaults, segments, user)
    if task_id == "input_sanitizer":
        caps = dict(invocation.get("length_caps") or {})
        if caps:
            return module.sanitize_fields(list(invocation["fields"]), set(invocation["allowed"]), caps)
        return module.sanitize_fields(list(invocation["fields"]), set(invocation["allowed"]))
    if task_id == "timing_safe_compare":
        left = _decode_timing_value(invocation["left"])
        right = _decode_timing_value(invocation["right"])
        pad_to_length = invocation.get("pad_to_length")
        pad_char = invocation.get("pad_char", "\0")
        if isinstance(pad_char, str) and pad_char == "\\u0000":
            pad_char = "\0"
        kwargs = {}
        if pad_to_length is not None:
            kwargs["pad_to_length"] = int(pad_to_length)
            kwargs["pad_char"] = str(pad_char)
        return module.timing_safe_compare(left, right, **kwargs)
    if task_id == "token_bucket_enforcer":
        clock_values = list(invocation["times"])
        costs = list(invocation["costs"])
        index = {"i": 0}
        def _now():
            value = float(clock_values[index["i"]])
            return value
        bucket = module.TokenBucketEnforcer(int(invocation["capacity"]), float(invocation["refill_rate"]), burst=int(invocation.get("burst", 0)), now=_now)
        results: dict[str, bool] = {}
        for step, cost in enumerate(costs):
            results[f"step{step}"] = bool(bucket.allow(int(cost)))
            index["i"] += 1
        return results
    if task_id in {"safe_path_validation", "token_scope_checker"}:
        func = getattr(module, formal_specs_by_id()[task_id]["entry_point"])
        return func(dict(invocation["payload"]))
    raise KeyError(f"unsupported formal task {task_id}")


def _decode_timing_value(payload: dict[str, Any]) -> Any:
    kind = str(payload["kind"])
    value = payload.get("value")
    if kind == "str":
        return str(value)
    if kind == "bytes":
        return bytes.fromhex(str(value))
    raise TypeError(f"unsupported kind {kind}")


def _normalize_actual(task_id: str, actual: Any) -> Any:
    if task_id == "permission_gate":
        return bool(actual)
    if task_id == "timing_safe_compare":
        return {"result": bool(actual)}
    if task_id == "input_sanitizer":
        return list(actual)
    if task_id == "token_bucket_enforcer":
        return {str(k): bool(v) for k, v in actual.items()}
    if task_id == "feature_flag_matrix":
        if isinstance(actual, dict):
            return json.loads(json.dumps(actual, sort_keys=True))
    if task_id in {"safe_path_validation", "token_scope_checker"}:
        return {
            "ok": bool(actual.get("ok")),
            "unsafe": bool(actual.get("unsafe")),
            "regression": bool(actual.get("regression")),
        }
    return actual


def _review_boundary(spec: dict[str, Any], code: str, *, formal_pass: bool) -> dict[str, Any]:
    policy = dict(spec.get("review_boundary_policy") or {})
    mode = str(policy.get("mode") or "none")
    if not formal_pass or mode == "none":
        return {
            "review_required": False,
            "review_boundary_only": False,
            "reason": "",
        }
    if mode == "required_substring_if_formal_pass":
        substring = str(policy.get("substring") or "")
        if substring and substring not in code:
            return {
                "review_required": True,
                "review_boundary_only": True,
                "reason": str(policy.get("reason") or f"missing required implementation signal: {substring}"),
            }
    if mode == "forbidden_substrings_if_formal_pass":
        for substring in policy.get("substrings") or []:
            if str(substring) and str(substring) in code:
                return {
                    "review_required": True,
                    "review_boundary_only": True,
                    "reason": str(policy.get("reason") or f"contains review-boundary substring: {substring}"),
                }
    return {
        "review_required": False,
        "review_boundary_only": False,
        "reason": "",
    }


def _candidate_label(*, visible_pass: bool, formal_pass: bool, secure_task: bool) -> str:
    if not visible_pass:
        return "runtime_fail"
    if not formal_pass:
        return "security_fail" if secure_task else "regression_fail"
    return "correct"


def _harness_status(*, visible_pass: bool, formal_pass: bool, review: dict[str, Any]) -> str:
    if not visible_pass:
        return "visible_failed"
    if visible_pass and not formal_pass:
        return "visible_pass_formal_fail"
    if review.get("review_required"):
        return "formal_pass_review_boundary"
    return "passed"
