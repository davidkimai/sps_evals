from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from specoracle.vericoding.regression_checks import is_regression_sensitive
from specoracle.vericoding.schemas import PROGRAM_VERSION, TaskRecord, stable_hash
from specoracle.vericoding.security_checks import SECURE_TASKS, hidden_oracle_hash

REPO_ROOT = Path(__file__).resolve().parents[3]


def build_task_pool(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    internal = _internal_tasks(repo_root)[:20]
    scbench = _scbench_tasks(repo_root)[:8]
    terminal = _terminal_tasks(repo_root)[:8]
    secure = _secure_tasks()

    dev_ids = {
        "internal": {task["task_id"] for task in internal[:4]},
        "scbench_regression": {task["task_id"] for task in scbench[:3]},
        "terminalbench_guardrail": {task["task_id"] for task in terminal[:2]},
        "secure": {task["task_id"] for task in secure[:3]},
    }

    tasks = []
    for surface, records in (
        ("internal", internal),
        ("scbench_regression", scbench),
        ("terminalbench_guardrail", terminal),
        ("secure", secure),
    ):
        for record in records:
            split = "dev" if record["task_id"] in dev_ids[surface] else "confirmatory"
            tasks.append(_task_record(surface=surface, split=split, **record).__dict__)

    manifest = {
        "schema_version": "vericoding_task_pool_v1",
        "program_version": PROGRAM_VERSION,
        "raw_content_committed": False,
        "target_count": 48,
        "actual_count": len(tasks),
        "surfaces": {
            "internal": len(internal),
            "scbench_regression": len(scbench),
            "terminalbench_guardrail": len(terminal),
            "secure": len(secure),
        },
        "limitations": _limitations(internal, scbench, terminal, secure),
        "tasks": tasks,
    }
    manifest["manifest_sha256"] = stable_hash({k: v for k, v in manifest.items() if k != "manifest_sha256"})
    return manifest


def split_manifest(task_pool: dict[str, Any], split: str) -> dict[str, Any]:
    tasks = [task for task in task_pool["tasks"] if task["split"] == split]
    manifest = {
        "schema_version": "vericoding_split_manifest_v1",
        "program_version": PROGRAM_VERSION,
        "split": split,
        "raw_content_committed": False,
        "task_count": len(tasks),
        "tasks": tasks,
    }
    manifest["manifest_sha256"] = stable_hash({k: v for k, v in manifest.items() if k != "manifest_sha256"})
    return manifest


def surface_manifest(task_pool: dict[str, Any], surface: str) -> dict[str, Any]:
    tasks = [task for task in task_pool["tasks"] if task["surface"] == surface]
    manifest = {
        "schema_version": "vericoding_surface_manifest_v1",
        "program_version": PROGRAM_VERSION,
        "surface": surface,
        "raw_content_committed": False,
        "task_count": len(tasks),
        "tasks": tasks,
    }
    manifest["manifest_sha256"] = stable_hash({k: v for k, v in manifest.items() if k != "manifest_sha256"})
    return manifest


def _task_record(
    *,
    surface: str,
    split: str,
    task_id: str,
    source_ref: str,
    task_hash: str,
    tags: list[str],
    summary: str,
) -> TaskRecord:
    return TaskRecord(
        program_version=PROGRAM_VERSION,
        surface=surface,  # type: ignore[arg-type]
        split=split,  # type: ignore[arg-type]
        task_id=task_id,
        stable_sample_id=f"vericoding:{surface}:{split}:{task_id}",
        role=summary,
        source_ref=source_ref,
        task_hash=task_hash,
        raw_content_committed=False,
        regression_sensitive=is_regression_sensitive(surface, tags),
        security_relevant=surface == "secure" or any("security" in tag.lower() for tag in tags),
        external_surface=surface in {"scbench_regression", "terminalbench_guardrail"},
    )


def _internal_tasks(repo_root: Path) -> list[dict[str, Any]]:
    out = []
    for path in sorted((repo_root / "data/slopbench").glob("*.yaml")):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        task_id = str(payload.get("id") or path.stem)
        tags = [str(tag) for tag in payload.get("tags", [])]
        out.append(
            {
                "task_id": task_id,
                "source_ref": f"data/slopbench/{path.name}",
                "task_hash": stable_hash(
                    {
                        "task_id": task_id,
                        "tags": tags,
                        "entry_point": payload.get("entry_point", "solution"),
                    }
                ),
                "tags": tags,
                "summary": "internal SlopBench task with tracked local tests",
            }
        )
    return out


def _scbench_tasks(repo_root: Path) -> list[dict[str, Any]]:
    path = repo_root / "runs/sprint9_external_subset_manifest.json"
    if not path.exists():
        return []
    manifest = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for problem in manifest.get("problems", []):
        task_id = str(problem["row_id"])
        tags = [str(tag) for tag in problem.get("tags", [])]
        out.append(
            {
                "task_id": task_id,
                "source_ref": "runs/sprint9_external_subset_manifest.json",
                "task_hash": str(problem.get("row_hash") or stable_hash(problem)),
                "tags": tags,
                "summary": "SCBench sanitized iterative-refinement regression episode",
            }
        )
    return out


def _terminal_tasks(repo_root: Path) -> list[dict[str, Any]]:
    paths = [
        repo_root / "runs/sprint10_closeout_v1/manifests/confirmatory_manifest.json",
        repo_root / "runs/sprint10_closeout_v1/manifests/dev_manifest.json",
    ]
    out = []
    seen = set()
    for path in paths:
        if not path.exists():
            continue
        manifest = json.loads(path.read_text(encoding="utf-8"))
        for task in manifest.get("tasks", []):
            task_id = str(task["task_id"])
            if task_id in seen:
                continue
            seen.add(task_id)
            tags = [str(tag) for tag in task.get("tags", [])]
            out.append(
                {
                    "task_id": task_id,
                    "source_ref": str(path.relative_to(repo_root)),
                    "task_hash": str(task.get("task_toml_sha256") or stable_hash(task)),
                    "tags": tags,
                    "summary": "Terminal-Bench structurally scorable Python guardrail task",
                }
            )
    return out


def _secure_tasks() -> list[dict[str, Any]]:
    return [
        {
            "task_id": task.task_id,
            "source_ref": "specoracle.vericoding.security_checks.SECURE_TASKS",
            "task_hash": hidden_oracle_hash(task.task_id),
            "tags": [task.category, "security"],
            "summary": task.summary,
        }
        for task in SECURE_TASKS
    ]


def _limitations(
    internal: list[dict[str, Any]],
    scbench: list[dict[str, Any]],
    terminal: list[dict[str, Any]],
    secure: list[dict[str, Any]],
) -> list[str]:
    limitations = []
    targets = {
        "internal": (internal, 20),
        "scbench_regression": (scbench, 8),
        "terminalbench_guardrail": (terminal, 8),
        "secure": (secure, 12),
    }
    for surface, (records, target) in targets.items():
        if len(records) < target:
            limitations.append(f"{surface} downgraded to {len(records)} of target {target}")
    return limitations
