from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from inspect_ai.dataset import MemoryDataset, Sample

SCBENCH_DATASET = "gabeorlanski/slopcodebench"
SCBENCH_CONFIG = "python"
SCBENCH_SPLIT = "test"
SCBENCH_REVISION = "5d067d6c497180081949cb9c0dc4502c9d750b1b"
SCBENCH_FINGERPRINT = "e8142880ace3f7d8"

_PRIORITY = ("nonzero_pass", "borderline_assertion_only", "hybrid_structural_delta")


def build_sprint9_external_subset_manifest(
    *,
    candidate_manifest_path: str | Path = "runs/sprint8_5_confirmation_subset_manifest.json",
    out_path: str | Path | None = None,
    max_problems: int = 8,
    neutral_manifest_path: str | Path = "runs/sprint8_5_breadth_hybrid_mini_all_12k/selection_manifest.json",
    neutral_controls: int = 2,
) -> dict[str, Any]:
    """Build a sanitized Sprint 9 external subset manifest from Sprint 8.5 candidates."""
    candidate_manifest = _read_json(_repo_path(candidate_manifest_path))
    candidates = list(candidate_manifest.get("problems") or [])
    selected = _select_prioritized_candidates(candidates, max_problems=max_problems)

    selected_ids = {str(item["row_id"]) for item in selected}
    neutral_items: list[dict[str, Any]] = []
    neutral_path = _repo_path(neutral_manifest_path)
    if neutral_controls > 0 and neutral_path.exists():
        neutral_manifest = _read_json(neutral_path)
        for problem in sorted(neutral_manifest.get("problems") or [], key=lambda item: item["row_id"]):
            row_id = str(problem.get("row_id") or "")
            if row_id in selected_ids:
                continue
            neutral = _sanitize_problem(problem, selection_reasons=["neutral_control"])
            neutral_items.append(neutral)
            selected_ids.add(row_id)
            if len(neutral_items) >= neutral_controls:
                break

    problems = [*_sort_for_manifest(selected), *neutral_items]
    manifest = {
        "schema": "specoracle.sprint9_external_subset.v1",
        "purpose": "diagnostic discriminative-subset recovery slice, not a representative external benchmark estimate",
        "raw_content_committed": False,
        "dataset": SCBENCH_DATASET,
        "config": SCBENCH_CONFIG,
        "split": SCBENCH_SPLIT,
        "revision": candidate_manifest.get("revision") or SCBENCH_REVISION,
        "fingerprint": (candidate_manifest.get("audit") or {}).get("fingerprint") or SCBENCH_FINGERPRINT,
        "selection_policy": {
            "priority_order": list(_PRIORITY),
            "max_problems": max_problems,
            "neutral_controls": len(neutral_items),
        },
        "problems": problems,
    }
    manifest["manifest_sha256"] = _hash_manifest(manifest)
    if out_path is not None:
        output = Path(out_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def load_scbench_manifest_samples(manifest_path: str | Path) -> MemoryDataset:
    """Load sanitized SCBench manifest rows as Inspect samples.

    The sample input deliberately contains no raw external prompt or test text.
    Paid/raw execution is handled by a separate runtime bridge and ignored logs,
    not by committed sample fixtures.
    """
    manifest = _read_json(_repo_path(manifest_path))
    samples = [
        Sample(
            id=str(problem["row_id"]),
            input=(
                f"SCBench external problem {problem['row_id']}.\n"
                "Raw benchmark instructions are quarantined and loaded only at execution time."
            ),
            target="",
            metadata={
                "benchmark": "scbench",
                "row_id": problem["row_id"],
                "row_hash": problem["row_hash"],
                "difficulty": problem.get("difficulty"),
                "tags": problem.get("tags", []),
                "selection_reasons": problem.get("selection_reasons", []),
                "checkpoint_count": problem.get("checkpoint_count"),
                "checkpoints": problem.get("checkpoints", []),
                "manifest_sha256": manifest.get("manifest_sha256"),
                "raw_content_committed": False,
            },
        )
        for problem in manifest.get("problems", [])
    ]
    return MemoryDataset(samples=samples, name="sprint9_scbench_subset")


def _select_prioritized_candidates(candidates: list[dict[str, Any]], *, max_problems: int) -> list[dict[str, Any]]:
    def rank(problem: dict[str, Any]) -> tuple[int, str]:
        reasons = set(problem.get("selection_reasons") or [])
        best = min((_PRIORITY.index(reason) for reason in reasons if reason in _PRIORITY), default=len(_PRIORITY))
        return best, str(problem.get("row_id") or "")

    return [
        _sanitize_problem(problem, selection_reasons=list(problem.get("selection_reasons") or []))
        for problem in sorted(candidates, key=rank)[:max_problems]
    ]


def _sanitize_problem(problem: dict[str, Any], *, selection_reasons: list[str]) -> dict[str, Any]:
    return {
        "row_id": str(problem["row_id"]),
        "row_hash": str(problem["row_hash"]),
        "language": str(problem.get("language") or "python"),
        "difficulty": str(problem.get("difficulty") or "unknown"),
        "tags": list(problem.get("tags") or []),
        "checkpoint_count": int(problem.get("checkpoint_count") or len(problem.get("checkpoints") or [])),
        "selection_reasons": selection_reasons,
        "checkpoints": [
            {
                "checkpoint_id": checkpoint["checkpoint_id"],
                "instruction_hash": checkpoint["instruction_hash"],
                "test_hash": checkpoint["test_hash"],
            }
            for checkpoint in problem.get("checkpoints", [])
        ],
    }


def _sort_for_manifest(problems: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(problems, key=lambda item: str(item["row_id"]))


def _hash_manifest(manifest: dict[str, Any]) -> str:
    payload = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _repo_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.exists():
        return candidate
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / candidate
