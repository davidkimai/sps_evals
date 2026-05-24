from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from specoracle.cli import load_tasks
from specoracle.vericoding.schemas import stable_hash

REPO_ROOT = Path(__file__).resolve().parents[3]
FORMAL_VARIANT = os.environ.get("SPECORACLE_FORMAL_VARIANT", "v2")
FORMAL_VARIANT_CONFIGS = {
    "v1": {
        "public_spec_path": REPO_ROOT / "data" / "vericoding_formal_public_specs.json",
        "program_version": "vericoding_formal_eval_v1",
        "default_root": Path("runs/vericoding_formal_eval_v1"),
    },
    "v2": {
        "public_spec_path": REPO_ROOT / "data" / "vericoding_formal_public_specs_v2.json",
        "program_version": "vericoding_formal_eval_v2",
        "default_root": Path("runs/vericoding_formal_eval_v2"),
    },
    "v2_2": {
        "public_spec_path": REPO_ROOT / "data" / "vericoding_formal_public_specs_v2_2.json",
        "program_version": "vericoding_formal_eval_v2_2",
        "default_root": Path("runs/vericoding_formal_eval_v2_2"),
    },
}
if FORMAL_VARIANT not in FORMAL_VARIANT_CONFIGS:
    raise ValueError(f"unsupported SPECORACLE_FORMAL_VARIANT: {FORMAL_VARIANT}")
FORMAL_PUBLIC_SPEC_PATH = FORMAL_VARIANT_CONFIGS[FORMAL_VARIANT]["public_spec_path"]
FORMAL_PROGRAM_VERSION = str(FORMAL_VARIANT_CONFIGS[FORMAL_VARIANT]["program_version"])
FORMAL_DEFAULT_ROOT = Path(FORMAL_VARIANT_CONFIGS[FORMAL_VARIANT]["default_root"])


def load_formal_public_specs(path: Path = FORMAL_PUBLIC_SPEC_PATH) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [dict(task) for task in payload.get("tasks", [])]


def formal_specs_by_id(path: Path = FORMAL_PUBLIC_SPEC_PATH) -> dict[str, dict[str, Any]]:
    return {str(task["task_id"]): task for task in load_formal_public_specs(path)}


def build_formal_task_pool() -> dict[str, Any]:
    tasks = []
    for task in load_formal_public_specs():
        task_id = str(task["task_id"])
        surface = str(task["surface"])
        split = str(task["split"])
        tasks.append(
            {
                "program_version": FORMAL_PROGRAM_VERSION,
                "surface": surface,
                "split": split,
                "task_id": task_id,
                "stable_sample_id": f"formal:{surface}:{split}:{task_id}",
                "role": str(task["formal_summary"]),
                "public_summary": str(_generation_public_spec(task)),
                "entry_point": str(task["entry_point"]),
                "source_ref": str(task["source_ref"]),
                "generation_surface_kind": str(task["generation_surface_kind"]),
                "generation_public_spec": str(_generation_public_spec(task)),
                "formal_generation_spec": str(task.get("formal_generation_spec") or task["formal_summary"]),
                "family_overrides": dict(task.get("family_overrides") or {}),
                "task_hash": stable_hash(
                    {
                        "task_id": task_id,
                        "surface": surface,
                        "split": split,
                        "generation_public_spec": _generation_public_spec(task),
                        "formal_summary": task["formal_summary"],
                        "formal_generation_spec": task.get("formal_generation_spec") or task["formal_summary"],
                        "visible_harness_kind": task["visible_harness_kind"],
                        "review_boundary_policy": task["review_boundary_policy"],
                        "family_overrides": task.get("family_overrides") or {},
                    }
                ),
                "raw_content_committed": False,
                "regression_sensitive": True,
                "security_relevant": surface == "secure" or "security" in task_id,
                "external_surface": False,
                "narrow_waist": True,
                "spec_coherent": True,
                "review_boundary_clear": True,
                "review_boundary_candidate": task.get("review_boundary_policy", {}).get("mode") != "none",
                "support_status": "unknown",
                "accepted_decision": "Accept only artifacts that satisfy visible behavior and formal evaluator cases without unresolved review-boundary blockers.",
                "rejected_decision": "Reject artifacts that pass visible checks but fail formal evaluator cases or secure boundary cases.",
                "human_review_required": str(task.get("review_boundary_policy", {}).get("reason") or "Review wrapper, interface, and deployment-boundary assumptions when the mechanized evaluator does not certify them."),
            }
        )
    manifest = {
        "schema": "specoracle.vericoding.formal_task_pool.v1",
        "program_version": FORMAL_PROGRAM_VERSION,
        "raw_content_committed": False,
        "task_count": len(tasks),
        "tasks": tasks,
    }
    manifest["manifest_sha256"] = stable_hash({k: v for k, v in manifest.items() if k != "manifest_sha256"})
    return manifest


def split_manifest(split: str) -> dict[str, Any]:
    task_pool = build_formal_task_pool()
    tasks = [task for task in task_pool["tasks"] if task["split"] == split]
    manifest = {
        "schema": "specoracle.vericoding.formal_split_manifest.v1",
        "program_version": FORMAL_PROGRAM_VERSION,
        "split": split,
        "raw_content_committed": False,
        "task_count": len(tasks),
        "tasks": tasks,
    }
    manifest["manifest_sha256"] = stable_hash({k: v for k, v in manifest.items() if k != "manifest_sha256"})
    return manifest


def _internal_tasks() -> dict[str, Any]:
    return {task.id: task for task in load_tasks(REPO_ROOT / "data/slopbench")}


def internal_visible_prompt(task_id: str) -> str:
    task = _internal_tasks().get(task_id)
    if task is None:
        raise KeyError(f"missing internal task {task_id}")
    return str(task.prompt)


def internal_visible_test_source(task_id: str) -> str:
    task = _internal_tasks().get(task_id)
    if task is None:
        raise KeyError(f"missing internal task {task_id}")
    return str(task.test_code)


def secure_visible_test_source(task_id: str) -> str:
    spec = formal_specs_by_id()[task_id]
    entry_point = str(spec["entry_point"])
    kind = str(spec["visible_harness_kind"])
    if kind == "secure_schema_only":
        payload = {"scope": "admin", "required_scope": "admin", "expires_at": 10, "now": 0}
        return (
            f"from solution import {entry_point}\n\n"
            f"def test_visible_schema_only():\n"
            f"    result = {entry_point}({payload!r})\n"
            f"    assert isinstance(result, dict)\n"
            f"    assert isinstance(result.get('ok'), bool)\n"
            f"    assert isinstance(result.get('unsafe'), bool)\n"
            f"    assert isinstance(result.get('regression'), bool)\n"
        )
    if kind == "secure_schema_and_benign":
        payload = {"path": "reports/summary.txt"}
        return (
            f"from solution import {entry_point}\n\n"
            f"def test_visible_schema_and_benign():\n"
            f"    result = {entry_point}({payload!r})\n"
            f"    assert isinstance(result, dict)\n"
            f"    assert isinstance(result.get('ok'), bool)\n"
            f"    assert isinstance(result.get('unsafe'), bool)\n"
            f"    assert isinstance(result.get('regression'), bool)\n"
            f"    assert result.get('unsafe') is False\n"
        )
    raise ValueError(f"unsupported secure visible harness kind: {kind}")


def visible_test_source(task_id: str) -> str:
    spec = formal_specs_by_id()[task_id]
    if spec["surface"] == "internal":
        return internal_visible_test_source(task_id)
    return secure_visible_test_source(task_id)


def _generation_public_spec(task: dict[str, Any]) -> str:
    kind = str(task["generation_surface_kind"])
    if kind == "internal_visible_yaml_prompt":
        return internal_visible_prompt(str(task["task_id"]))
    if kind == "secure_visible_public_summary":
        summary = str(task.get("generator_public_summary") or "")
        constraints = " ".join(str(item) for item in task.get("generator_public_constraints") or [])
        return f"Task: {summary} Constraints: {constraints}".strip()
    raise ValueError(f"unsupported generation surface kind: {kind}")
