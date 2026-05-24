from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from openai import OpenAI

from specoracle.cli import load_tasks
from specoracle.config import Task
from specoracle.generator import extract_python_code
from specoracle.metrics import build_structural_metric_record
from specoracle.vericoding.runtime_env import estimate_openai_cost, extract_usage
from specoracle.vericoding.schemas import (
    LIVE_PROGRAM_VERSION,
    file_sha256,
    now_iso,
    stable_hash,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
VISIBLE_SECURE_SPEC_PATH = REPO_ROOT / "data" / "vericoding_visible_secure_specs.json"
FORBIDDEN_PROMPT_SOURCE_FILES = (
    "src/specoracle/vericoding/hidden_oracles.py",
    "src/specoracle/vericoding/harnesses.py",
    "artifacts/*hidden_oracles*",
    "post_failure_casebooks",
)


GENERATION_CONDITIONS = {
    "internal": (
        "baseline_prompt",
        "spec_conditioned_prompt",
        "structural_discipline_prompt",
        "concise_prompt",
        "requirements_first_prompt",
        "alt_seed_or_temp_prompt",
    ),
    "secure": (
        "baseline_prompt",
        "spec_conditioned_prompt",
        "structural_discipline_prompt",
        "concise_prompt",
        "requirements_first_prompt",
        "alt_seed_or_temp_prompt",
    ),
    "scbench_regression": (
        "baseline_scbench_prompt",
        "spec_conditioned_scbench_prompt",
        "regression_preservation_prompt",
        "concise_scbench_prompt",
    ),
    "terminalbench_guardrail": (
        "baseline_terminal_agent",
        "portable_structural_prompt_condition",
        "requirements_first_terminal_prompt",
    ),
}

CONDITION_INSTRUCTIONS = {
    "baseline_prompt": "Direct implementation: implement the requested entry point plainly and satisfy the visible contract.",
    "spec_conditioned_prompt": "Spec-conditioned implementation: identify the acceptance boundary before writing code.",
    "structural_discipline_prompt": "Structure-first implementation: use small helpers, explicit branches, and auditable control flow.",
    "concise_prompt": "Concise implementation: minimize moving parts while preserving all public constraints.",
    "requirements_first_prompt": "Requirements-first implementation: list the public requirements mentally, then implement the complete function.",
    "invariants_first_prompt": "Invariants-first implementation: identify input/output invariants and preserve them explicitly in code.",
    "regression_preservation_prompt": "Regression-preservation implementation: preserve backwards-compatible edge-case behavior and avoid broad rewrites.",
    "decomposition_first_prompt": "Decomposition-first implementation: split parsing, validation, and decision logic into small named helpers.",
    "self_critique_prompt": "Self-critique implementation: mentally check for bypasses, edge cases, and overbroad acceptance before emitting final code.",
    "alt_seed_or_temp_prompt": "Diverse alternate implementation: use a different decomposition or edge-case strategy than a direct baseline.",
    "baseline_scbench_prompt": "Direct public regression task implementation using only sanitized public metadata.",
    "spec_conditioned_scbench_prompt": "Spec-conditioned public regression implementation using only sanitized public metadata.",
    "regression_preservation_prompt": "Regression-preservation implementation: prioritize backward-compatible behavior from the visible summary.",
    "concise_scbench_prompt": "Concise public regression implementation using only sanitized public metadata.",
    "baseline_terminal_agent": "Direct terminal-task implementation using only sanitized public metadata.",
    "portable_structural_prompt_condition": "Portable structural implementation: avoid environment-specific assumptions.",
    "requirements_first_terminal_prompt": "Requirements-first terminal implementation using only sanitized public metadata.",
    "internal_attack_invariants_prompt": "Internal support attack: implement from explicit invariants, preserving edge-case semantics and rejecting underspecified shortcuts.",
    "internal_attack_boundary_cases_prompt": "Internal support attack: reason through boundary cases before coding, including empty inputs, limits, tie cases, and error handling.",
    "internal_attack_reference_model_prompt": "Internal support attack: build a small reference-model style implementation that favors semantic clarity over cleverness.",
    "internal_attack_minimal_patch_prompt": "Internal support attack: write the smallest complete implementation that preserves the visible API while avoiding broad behavioral assumptions.",
    "internal_attack_property_table_prompt": "Internal support attack: derive a compact input/property table mentally, then implement each branch explicitly.",
    "internal_attack_error_semantics_prompt": "Internal support attack: prioritize exact error, precedence, ordering, and regression semantics over happy-path behavior.",
}


def generate_live_candidate(
    task: dict[str, Any],
    *,
    condition: str,
    sample_index: int,
    model: str,
    artifact_dir: Path,
    provenance: dict[str, Any],
    program_version: str = LIVE_PROGRAM_VERSION,
    evaluation_mode: str = "proxy",
    claim_bearing: bool = False,
    candidate_condition_id: str | None = None,
    extra_lineage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if claim_bearing and evaluation_mode != "real_harness":
        raise ValueError("claim-bearing generation requires evaluation_mode='real_harness'")
    start = time.monotonic()
    prompt = _prompt_for_task(task, condition=condition)
    client = OpenAI(timeout=45.0)
    response = None
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = client.responses.create(
                model=model,
                instructions=_system_prompt(condition),
                input=prompt,
                temperature=0.3 if "alt_seed" in condition else 0.2,
                max_output_tokens=1600,
            )
            break
        except Exception as exc:  # Provider/network failures should not corrupt append-only ledgers.
            last_error = exc
            if attempt == 2:
                raise
            time.sleep(2.0 * (attempt + 1))
    if response is None:
        raise RuntimeError("OpenAI response was not returned") from last_error
    usage = extract_usage(response)
    text = _response_text(response)
    code = extract_python_code(text)
    extraction_failed = not code.strip()
    if extraction_failed and claim_bearing:
        code = ""
    elif extraction_failed:
        code = _fallback_code(task)
    candidate_condition = candidate_condition_id or condition
    candidate_id = f"{task['task_id']}:{candidate_condition}:live{sample_index}"
    bank_row_id = stable_hash(
        {
            "program_version": program_version,
            "task_id": task["task_id"],
            "condition": candidate_condition,
            "sample_index": sample_index,
        },
        length=18,
    )
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / f"{bank_row_id}.py"
    if code.strip():
        artifact_path.write_text(code, encoding="utf-8")
        artifact_sha256 = file_sha256(artifact_path)
        metrics = build_structural_metric_record(code, language="python")
        evals = _evaluate_candidate(task, code, metrics, evaluation_mode=evaluation_mode)
    else:
        artifact_sha256 = ""
        metrics = build_structural_metric_record("", language="python")
        evals = _extraction_failure_evals()
    row = {
        "program_version": program_version,
        "bank_row_id": bank_row_id,
        "surface": task["surface"],
        "split": task["split"],
        "task_id": task["task_id"],
        "stable_sample_id": task["stable_sample_id"],
        "candidate_id": candidate_id,
        "candidate_source_type": "live_model",
        "primary_evidence": True,
        "candidate_source": "openai_responses",
        "candidate_lineage": f"live_model:{candidate_condition}:{sample_index}",
        "generator_condition": condition,
        "candidate_condition_id": candidate_condition,
        "generator_provider": "openai",
        "generator_model": model,
        "prompt_template_version": "vericoding_live_generation_v2",
        "prompt_provenance": prompt_provenance_for_task(task),
        "evaluation_mode": evaluation_mode,
        "claim_bearing": claim_bearing,
        "fallback_used": bool(extraction_failed and not claim_bearing),
        "generation_outcome": "extraction_failed" if extraction_failed else "code_extracted",
        "temperature": 0.3 if "alt_seed" in condition else 0.2,
        "seed": sample_index,
        "raw_artifact_policy": "tracked_generated_candidate_no_external_raw_prompt",
        "candidate_artifact_path": str(artifact_path) if code.strip() else "",
        "candidate_sha256": artifact_sha256,
        "code_summary": _code_summary(code),
        "visible_compile_pass": bool(metrics["parse_ok"]),
        "visible_tests_pass": evals["visible_tests_pass"],
        "visible_proxy_checks_pass": evals["visible_proxy_checks_pass"],
        "visible_regression_proxy_pass": evals["visible_regression_proxy_pass"],
        "visible_security_proxy_pass": evals["visible_security_proxy_pass"],
        "hidden_tests_pass": evals["hidden_tests_pass"],
        "property_checks_pass": evals["property_checks_pass"],
        "regression_checks_pass": evals["regression_checks_pass"],
        "security_checks_pass": evals["security_checks_pass"],
        "parse_ok": bool(metrics["parse_ok"]),
        "cc_average": metrics.get("cc_average"),
        "max_nesting_depth": metrics.get("max_nesting_depth"),
        "maintainability_index": metrics.get("maintainability_index"),
        "redundancy_score": metrics.get("redundancy_score"),
        "candidate_label": evals["candidate_label"],
        "deceptive_candidate": evals["deceptive_candidate"],
        "insecure_candidate": evals["insecure_candidate"],
        "regression_candidate": evals["regression_candidate"],
        "surface_evidence_quality": evals.get("surface_evidence_quality", "proxy_heuristic"),
        "harness_status": evals.get("harness_status", ""),
        "visible_harness": evals.get("visible_harness", {}),
        "hidden_harness": evals.get("hidden_harness", {}),
        "cost_usd": estimate_openai_cost(
            model,
            usage["input_tokens"],
            usage["output_tokens"],
            cached_input_tokens=usage["cached_input_tokens"],
        ),
        "input_tokens": usage["input_tokens"],
        "cached_input_tokens": usage["cached_input_tokens"],
        "output_tokens": usage["output_tokens"],
        "wall_seconds": round(max(0.001, time.monotonic() - start), 3),
        "live_call_id": str(getattr(response, "id", "")),
        "runner_git_commit": provenance["runner_git_commit"],
        "runner_git_dirty": provenance["runner_git_dirty"],
        "diff_fingerprint": provenance["diff_fingerprint"],
        "dirty_override": provenance["dirty_override"],
        "created_at": now_iso(),
    }
    if extra_lineage:
        row.update(extra_lineage)
    return row


def repair_candidate_live(
    candidate: dict[str, Any],
    *,
    task: dict[str, Any],
    model: str,
    repair_dir: Path,
    provenance: dict[str, Any],
    program_version: str = LIVE_PROGRAM_VERSION,
    evaluation_mode: str = "proxy",
    claim_bearing: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if claim_bearing and evaluation_mode != "real_harness":
        raise ValueError("claim-bearing repair requires evaluation_mode='real_harness'")
    start = time.monotonic()
    original_code = Path(candidate["candidate_artifact_path"]).read_text(encoding="utf-8")
    prompt = {
        "task_summary": _task_summary(task),
        "selected_candidate_id": candidate["candidate_id"],
        "visible_failure_context": {
            "visible_tests_pass": candidate.get("visible_tests_pass"),
            "parse_ok": candidate.get("parse_ok"),
            "cc_average": candidate.get("cc_average"),
        },
        "candidate_code": original_code,
        "instruction": "Return a repaired complete Python module only.",
    }
    client = OpenAI()
    response = client.responses.create(
        model=model,
        instructions="You are performing one bounded CEGIS-lite repair. Return only Python code.",
        input=json.dumps(prompt, sort_keys=True),
        max_output_tokens=1200,
    )
    usage = extract_usage(response)
    repaired_code = extract_python_code(_response_text(response)) or original_code
    repair_row_id = stable_hash(
        {
            "program_version": program_version,
            "candidate_id": candidate["candidate_id"],
            "task_id": task["task_id"],
            "repair": "v2",
        },
        length=18,
    )
    repair_dir.mkdir(parents=True, exist_ok=True)
    repair_path = repair_dir / f"{repair_row_id}.py"
    repair_path.write_text(repaired_code, encoding="utf-8")
    metrics = build_structural_metric_record(repaired_code, language="python")
    evals = _evaluate_candidate(task, repaired_code, metrics, evaluation_mode=evaluation_mode)
    repaired_candidate = dict(candidate)
    repaired_candidate.update(
        {
            "candidate_id": f"{candidate['candidate_id']}:repair1",
            "candidate_artifact_path": str(repair_path),
            "candidate_sha256": file_sha256(repair_path),
            "parse_ok": bool(metrics["parse_ok"]),
            "cc_average": metrics.get("cc_average"),
            "max_nesting_depth": metrics.get("max_nesting_depth"),
            "maintainability_index": metrics.get("maintainability_index"),
            "redundancy_score": metrics.get("redundancy_score"),
            **evals,
        }
    )
    repair_row = {
        "adjudication_row_id": repair_row_id,
        "program_version": program_version,
        "task_id": task["task_id"],
        "selected_candidate_id": candidate["candidate_id"],
        "repaired_candidate_id": repaired_candidate["candidate_id"],
        "repair_prompt_hash": stable_hash(prompt),
        "provider": "openai",
        "model": model,
        "incremental_cost_usd": estimate_openai_cost(
            model,
            usage["input_tokens"],
            usage["output_tokens"],
            cached_input_tokens=usage["cached_input_tokens"],
        ),
        "input_tokens": usage["input_tokens"],
        "cached_input_tokens": usage["cached_input_tokens"],
        "output_tokens": usage["output_tokens"],
        "wall_seconds": round(max(0.001, time.monotonic() - start), 3),
        "repaired_artifact_path": str(repair_path),
        "repaired_artifact_sha256": file_sha256(repair_path),
        "reevaluation_results": {
            key: repaired_candidate[key]
            for key in (
                "visible_tests_pass",
                "hidden_tests_pass",
                "property_checks_pass",
                "regression_checks_pass",
                "security_checks_pass",
                "candidate_label",
            )
        },
        "live_call_id": str(getattr(response, "id", "")),
        "runner_git_commit": provenance["runner_git_commit"],
        "runner_git_dirty": provenance["runner_git_dirty"],
        "diff_fingerprint": provenance["diff_fingerprint"],
        "dirty_override": provenance["dirty_override"],
        "created_at": now_iso(),
    }
    validate_repair_audit(candidate, repaired_candidate, repair_row)
    return repaired_candidate, repair_row


def validate_repair_audit(
    original_candidate: dict[str, Any],
    repaired_candidate: dict[str, Any],
    repair_row: dict[str, Any],
) -> None:
    hidden_fields = (
        "hidden_tests_pass",
        "property_checks_pass",
        "regression_checks_pass",
        "security_checks_pass",
        "candidate_label",
    )
    changed = any(original_candidate.get(field) != repaired_candidate.get(field) for field in hidden_fields)
    if not changed:
        return
    artifact_path = Path(str(repair_row.get("repaired_artifact_path") or ""))
    if not artifact_path.exists():
        raise RuntimeError("repair changed adjudication fields without a materialized repaired artifact")
    if file_sha256(artifact_path) != repair_row.get("repaired_artifact_sha256"):
        raise RuntimeError("repair changed adjudication fields with mismatched repaired artifact hash")
    reevaluation = repair_row.get("reevaluation_results") or {}
    missing = [field for field in hidden_fields if field not in reevaluation]
    if missing:
        raise RuntimeError(f"repair changed adjudication fields without reevaluation fields: {missing}")


def _prompt_for_task(task: dict[str, Any], *, condition: str) -> str:
    return json.dumps(
        {
            "task_id": task["task_id"],
            "surface": task["surface"],
            "summary": _task_summary(task),
            "condition": condition,
            "generation_family_instruction": CONDITION_INSTRUCTIONS.get(condition, "Implement the requested entry point."),
            "entry_point": _entry_point(task),
            "constraints": [
                "Return Python code only.",
                "Use standard library only.",
                "Do not include tests.",
                "Prefer explicit, auditable control flow.",
            ],
        },
        sort_keys=True,
    )


def _system_prompt(condition: str) -> str:
    return (
        "You are a secure program synthesis engineer. Generate one complete Python module. "
        f"Condition: {condition}. {CONDITION_INSTRUCTIONS.get(condition, '')} Return code only, no markdown. Keep the implementation compact; "
        "prefer one public entry point and a few small helpers over a broad framework."
    )


def _task_summary(task: dict[str, Any]) -> str:
    surface = task["surface"]
    if surface == "internal":
        local = _local_task(str(task["task_id"]))
        if local:
            return local.prompt[:1800]
    if surface == "secure":
        return _visible_secure_task_contract(str(task["task_id"]))[:1800]
    return str(task.get("role") or task.get("source_ref") or task["task_id"])[:1800]


def prompt_provenance_for_task(task: dict[str, Any]) -> dict[str, Any]:
    surface = str(task["surface"])
    if surface == "secure":
        allowed = [str(VISIBLE_SECURE_SPEC_PATH.relative_to(REPO_ROOT))]
    elif surface == "internal":
        allowed = ["data/slopbench/*.yaml"]
    else:
        allowed = ["frozen manifest visible fields", "sanitized public integration metadata"]
    return {
        "surface": surface,
        "allowed_prompt_sources": allowed,
        "forbidden_prompt_sources": list(FORBIDDEN_PROMPT_SOURCE_FILES),
        "hidden_evaluator_sources_used": [],
    }


def _visible_secure_task_contract(task_id: str) -> str:
    spec = _visible_secure_specs().get(task_id)
    func = _entry_point({"surface": "secure", "task_id": task_id})
    if not spec:
        return (
            f"Implement {func}(payload: dict) -> dict for a security-sensitive validator. "
            "Return {'ok': bool, 'unsafe': bool, 'regression': bool}. Do not perform external side effects."
        )
    constraints = " ".join(str(item) for item in spec.get("public_constraints", []))
    return (
        f"Implement {spec.get('entry_point') or func}(payload: dict) -> dict. "
        f"Task: {spec.get('public_summary', 'Validate a security-sensitive payload.')} "
        f"Constraints: {constraints}"
    )


def _visible_secure_specs() -> dict[str, dict[str, Any]]:
    if not VISIBLE_SECURE_SPEC_PATH.exists():
        return {}
    payload = json.loads(VISIBLE_SECURE_SPEC_PATH.read_text(encoding="utf-8"))
    return {str(row["task_id"]): dict(row) for row in payload.get("tasks", [])}


def _local_task(task_id: str) -> Task | None:
    try:
        tasks = load_tasks(REPO_ROOT / "data/slopbench")
    except Exception:
        return None
    by_id = {task.id: task for task in tasks}
    return by_id.get(task_id)


def _entry_point(task: dict[str, Any]) -> str:
    if task["surface"] == "internal":
        local = _local_task(str(task["task_id"]))
        if local:
            return local.entry_point
    return f"solution_{str(task['task_id']).replace('-', '_')}"


def _evaluate_candidate(
    task: dict[str, Any],
    code: str,
    metrics: dict[str, Any],
    *,
    evaluation_mode: str,
) -> dict[str, Any]:
    if evaluation_mode == "real_harness":
        from specoracle.vericoding.harnesses import evaluate_candidate_real

        return evaluate_candidate_real(task, code, metrics)
    parse_ok = bool(metrics["parse_ok"])
    visible_tests = parse_ok and "raise NotImplementedError" not in code
    hidden_tests = visible_tests
    property_checks = visible_tests
    regression_checks = visible_tests and "regression" not in code
    security_checks = visible_tests and "unsafe" not in code
    if task["surface"] == "secure" and parse_ok:
        from specoracle.vericoding.hidden_oracles import run_hidden_oracle

        hidden = run_hidden_oracle(str(task["task_id"]), code)
        hidden_tests = bool(hidden["hidden_passed"])
        property_checks = hidden_tests
        security_checks = hidden_tests
    if task["surface"] == "scbench_regression":
        hidden_tests = False
        regression_checks = visible_tests and "regression" not in code
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


def _fallback_code(task: dict[str, Any]) -> str:
    func = _entry_point(task)
    return f"def {func}(payload=None):\n    return {{'ok': True, 'payload': payload}}\n"


def _extraction_failure_evals() -> dict[str, Any]:
    return {
        "visible_tests_pass": False,
        "visible_proxy_checks_pass": False,
        "visible_regression_proxy_pass": False,
        "visible_security_proxy_pass": False,
        "hidden_tests_pass": False,
        "property_checks_pass": False,
        "regression_checks_pass": False,
        "security_checks_pass": False,
        "candidate_label": "syntax_fail",
        "deceptive_candidate": False,
        "insecure_candidate": False,
        "regression_candidate": False,
        "surface_evidence_quality": "real_harness",
        "harness_status": "generation_extraction_failed",
    }


def _code_summary(code: str) -> str:
    return " ".join(line.strip() for line in code.splitlines()[:8])[:500]


def _response_text(response: Any) -> str:
    text = getattr(response, "output_text", None)
    if text:
        return str(text)
    if hasattr(response, "model_dump"):
        payload = response.model_dump()
        chunks: list[str] = []
        for item in payload.get("output", []):
            for content in item.get("content", []):
                if content.get("text"):
                    chunks.append(str(content["text"]))
        return "\n".join(chunks)
    return str(response)
