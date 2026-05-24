from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from inspect_ai.dataset import MemoryDataset, Sample

from specoracle.vericoding.formal_specs import FORMAL_DEFAULT_ROOT, FORMAL_PROGRAM_VERSION


def load_formal_eval_samples(
    root: str | Path = FORMAL_DEFAULT_ROOT,
    *,
    split: str = "confirmatory",
    phase: str = "confirmatory",
) -> MemoryDataset:
    repo_root = _repo_path(root)
    manifest_name = "formal_dev_manifest.json" if split == "dev" else "formal_confirmatory_manifest.json"
    manifest = _read_json(repo_root / "manifests" / manifest_name)
    tasks = list(manifest.get("tasks", []))
    candidates = _read_jsonl(repo_root / "ledgers" / "candidate_bank.jsonl")
    selectors = _read_jsonl(repo_root / "ledgers" / "selector_eval.jsonl")
    e2e = _read_jsonl(repo_root / "ledgers" / "e2e_runs.jsonl")
    formal = _read_jsonl(repo_root / "ledgers" / "formal_eval.jsonl")
    support = []
    for task in tasks:
        task_id = str(task["task_id"])
        task_candidates = [row for row in candidates if row.get("task_id") == task_id and row.get("split") == split]
        task_selectors = [row for row in selectors if row.get("task_id") == task_id and row.get("split") == split]
        task_e2e = [row for row in e2e if row.get("task_id") == task_id and row.get("split") == split]
        task_formal = [row for row in formal if row.get("task_id") == task_id and row.get("split") == split]
        visible_formal_fail = sum(bool(row.get("visible_tests_pass")) and not bool(row.get("formal_pass")) for row in task_candidates)
        hidden_support = sum(bool(row.get("formal_pass")) for row in task_candidates)
        support.append(
            Sample(
                id=str(task["stable_sample_id"]),
                input=f"Formal vericoding task {task_id} ({phase}).",
                target="",
                metadata={
                    "schema": "specoracle.vericoding.formal.inspect_sample.v1",
                    "task_id": task_id,
                    "surface": task.get("surface"),
                    "split": split,
                    "stable_sample_id": task.get("stable_sample_id"),
                    "program_version": task.get("program_version", FORMAL_PROGRAM_VERSION),
                    "inspect_source": "formal_eval_v1",
                    "candidate_ledger_rows": len(task_candidates),
                    "selector_ledger_rows": len(task_selectors),
                    "e2e_ledger_rows": len(task_e2e),
                    "formal_ledger_rows": len(task_formal),
                    "hidden_support_count": hidden_support,
                    "secure_support_count": hidden_support if task.get("surface") == "secure" else 0,
                    "visible_hidden_fail_count": visible_formal_fail,
                    "secure_false_accept_candidate_count": sum(bool(row.get("insecure_candidate")) and bool(row.get("visible_tests_pass")) for row in task_candidates),
                    "raw_content_committed": False,
                    "narrow_waist": task.get("narrow_waist"),
                    "review_boundary_clear": task.get("review_boundary_clear"),
                    "support_status": "support_present" if hidden_support else "support_absent",
                    "secure_challenge_eligible": task.get("surface") == "secure",
                    "accepted_decision": task.get("accepted_decision"),
                    "rejected_decision": task.get("rejected_decision"),
                    "human_review_required": task.get("human_review_required"),
                    "spec_coherent": task.get("spec_coherent"),
                },
            )
        )
    return MemoryDataset(samples=support, name=f"formal_eval_{phase}_{split}")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _repo_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.exists() or candidate.is_absolute():
        return candidate
    return Path(__file__).resolve().parents[3] / candidate
