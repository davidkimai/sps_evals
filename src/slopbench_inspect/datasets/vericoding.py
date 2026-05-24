from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from inspect_ai.dataset import MemoryDataset, Sample

DEFAULT_VERICODING_ROOT = Path("runs/vericoding_research_v3")


def load_vericoding_samples(
    root: str | Path = DEFAULT_VERICODING_ROOT,
    *,
    surface: str | None = None,
    split: str = "confirmatory",
    condition: str = "summary",
    source: str = "task_pool",
) -> MemoryDataset:
    """Load sanitized vericoding manifests and summaries as Inspect samples."""
    repo_root = _repo_path(root)
    tasks = _load_tasks(repo_root, source=source)
    candidates = _read_csv(repo_root / "data/wrangled/candidate_summary.csv")
    selector_rows = _read_csv(repo_root / "data/wrangled/selector_summary.csv")
    e2e_rows = _read_csv(repo_root / "data/wrangled/e2e_summary.csv")
    candidate_ledger = _read_jsonl(repo_root / "ledgers/candidate_bank.jsonl")
    selector_ledger = _read_jsonl(repo_root / "ledgers/selector_eval.jsonl")
    e2e_ledger = _read_jsonl(repo_root / "ledgers/e2e_runs.jsonl")
    secure_ledger = _read_jsonl(repo_root / "ledgers/secure_eval.jsonl")
    external_ledger = _read_jsonl(repo_root / "ledgers/external_guardrail.jsonl")
    formal_ledger = _read_jsonl(repo_root / "ledgers/formal_slice_eval.jsonl")
    samples = []
    for task in tasks:
        if task.get("split") != split:
            continue
        if surface and task.get("surface") != surface:
            continue
        stable_id = str(task["stable_sample_id"])
        evidence = _task_evidence(
            task,
            candidates=candidate_ledger,
            selectors=selector_ledger,
            e2e=e2e_ledger,
            secure=secure_ledger,
            external=external_ledger,
            formal=formal_ledger,
        )
        samples.append(
            Sample(
                id=stable_id,
                input=(
                    f"Vericoding task {task['task_id']} on surface {task['surface']}.\n"
                    "Raw external prompts, tests, assertions, and hidden oracles are not committed."
                ),
                target="",
                metadata={
                    "schema": "specoracle.vericoding.inspect_sample.v1",
                    "surface": task["surface"],
                    "split": task["split"],
                    "task_id": task["task_id"],
                    "condition": condition,
                    "program_version": task.get("program_version", "vericoding_research_v3"),
                    "stable_sample_id": stable_id,
                    "raw_content_committed": False,
                    "candidate_summary_rows": len(candidates),
                    "selector_summary_rows": len(selector_rows),
                    "e2e_summary_rows": len(e2e_rows),
                    **evidence,
                    "task_hash": task.get("task_hash"),
                    "regression_sensitive": task.get("regression_sensitive"),
                    "security_relevant": task.get("security_relevant"),
                    "basin": task.get("basin"),
                    "secure_challenge": task.get("secure_challenge"),
                    "narrow_waist": task.get("narrow_waist"),
                    "spec_coherent": task.get("spec_coherent"),
                    "review_boundary_clear": task.get("review_boundary_clear"),
                    "support_status": task.get("support_status"),
                    "secure_challenge_eligible": task.get("secure_challenge_eligible"),
                    "review_boundary_candidate": task.get("review_boundary_candidate"),
                    "accepted_decision": task.get("accepted_decision"),
                    "rejected_decision": task.get("rejected_decision"),
                    "human_review_required": task.get("human_review_required"),
                    "component_family": task.get("component_family"),
                    "inspect_source": source,
                },
            )
        )
    return MemoryDataset(samples=samples, name=f"vericoding_{source}_{split}_{surface or 'all'}")


def _load_tasks(root: Path, *, source: str) -> list[dict[str, Any]]:
    if source == "primary_core":
        manifest = _read_json(root / "manifests/primary_core_task_pool.json")
    elif source == "internal_regression":
        manifest = _read_json(root / "manifests/internal_basin_manifest.json")
        if not manifest.get("tasks"):
            manifest = _read_json(root / "manifests/internal_regression_manifest.json")
    elif source in {"secure", "secure_rejection"}:
        manifest = _read_json(root / "manifests/secure_rejection_manifest.json")
        if not manifest.get("tasks"):
            manifest = _read_json(root / "manifests/task_pool.json")
    elif source == "secure_challenge":
        manifest = _read_json(root / "manifests/secure_challenge_manifest.json")
        if not manifest.get("tasks"):
            manifest = _read_json(root / "manifests/secure_rejection_manifest.json")
    elif source == "formal_overlay":
        manifest = _read_json(root / "manifests/formal_overlay_manifest.json")
        if not manifest.get("tasks"):
            manifest = _read_json(root / "manifests/task_pool.json")
    elif source == "external_guardrail":
        manifest = _read_json(root / "manifests/terminalbench_guardrail_manifest.json")
        if not manifest.get("tasks"):
            manifest = _read_json(root / "manifests/task_pool.json")
    elif source in {"scbench_regression", "scbench_transfer"}:
        manifest = _read_json(root / "manifests/scbench_transfer_manifest.json")
        if not manifest.get("tasks"):
            manifest = _read_json(root / "manifests/scbench_regression_manifest.json")
    else:
        manifest = _read_json(root / "manifests/task_pool.json")
    return list(manifest.get("tasks", []))


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"tasks": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _task_evidence(
    task: dict[str, Any],
    *,
    candidates: list[dict[str, Any]],
    selectors: list[dict[str, Any]],
    e2e: list[dict[str, Any]],
    secure: list[dict[str, Any]],
    external: list[dict[str, Any]],
    formal: list[dict[str, Any]],
) -> dict[str, Any]:
    task_id = str(task.get("task_id"))
    surface = str(task.get("surface"))
    split = str(task.get("split"))
    task_candidates = [
        row for row in candidates
        if row.get("task_id") == task_id and row.get("surface") == surface and row.get("split") == split
    ]
    task_selectors = [
        row for row in selectors
        if row.get("task_id") == task_id and row.get("surface") == surface and row.get("split") == split
    ]
    task_e2e = [
        row for row in e2e
        if row.get("task_id") == task_id and row.get("surface") == surface and row.get("split") == split
    ]
    task_secure = [row for row in secure if row.get("task_id") == task_id]
    task_formal = [row for row in formal if row.get("task_id") == task_id]
    visible_hidden_fail = [
        row for row in task_candidates
        if bool(row.get("visible_tests_pass")) and not bool(row.get("hidden_tests_pass"))
    ]
    secure_false_accept_candidates = [
        row for row in task_candidates
        if bool(row.get("visible_tests_pass")) and not bool(row.get("security_checks_pass"))
    ]
    return {
        "candidate_ledger_rows": len(task_candidates),
        "selector_ledger_rows": len(task_selectors),
        "e2e_ledger_rows": len(task_e2e),
        "secure_ledger_rows": len(task_secure),
        "formal_ledger_rows": len(task_formal),
        "external_ledger_rows": len(external) if surface == "terminalbench_guardrail" else 0,
        "hidden_support_count": sum(bool(row.get("hidden_tests_pass")) for row in task_candidates),
        "secure_support_count": sum(bool(row.get("security_checks_pass")) for row in task_candidates),
        "regression_clean_count": sum(bool(row.get("regression_checks_pass")) for row in task_candidates),
        "visible_hidden_fail_count": len(visible_hidden_fail),
        "secure_false_accept_candidate_count": len(secure_false_accept_candidates),
        "visible_pass_count": sum(bool(row.get("visible_tests_pass")) for row in task_candidates),
    }


def _repo_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.exists() or candidate.is_absolute():
        return candidate
    return Path(__file__).resolve().parents[3] / candidate
