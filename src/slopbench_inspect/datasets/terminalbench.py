from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from inspect_ai.dataset import MemoryDataset, Sample


DEFAULT_CLOSEOUT_ROOT = Path("runs/sprint10_closeout_v1")


def load_terminalbench_python_slice_samples(
    closeout_root: str | Path = DEFAULT_CLOSEOUT_ROOT,
    *,
    slice_name: str = "dev",
    condition: str = "baseline",
) -> MemoryDataset:
    """Load sanitized Terminal-Bench closeout rows as Inspect samples.

    The sample identity deliberately excludes condition so baseline and portable
    condition rows can be paired against the same task.
    """
    root = _repo_path(closeout_root)
    manifest = _read_json(root / f"manifests/{slice_name}_manifest.json")
    summary_rows = _read_csv_like_json(root / "data/wrangled/summary.csv")
    by_task = {
        str(row.get("task_id")): row
        for row in summary_rows
        if row.get("slice") == slice_name and row.get("condition") == condition
    }
    samples = []
    for task in manifest.get("tasks", []):
        task_id = str(task["task_id"])
        stable_id = str(task.get("stable_sample_id") or f"terminalbench:{slice_name}:{task_id}")
        row = by_task.get(task_id, {})
        samples.append(
            Sample(
                id=stable_id,
                input=(
                    f"Terminal-Bench Python-slice task {task_id}.\n"
                    "Raw task instructions, tests, terminal logs, and transcripts are "
                    "quarantined outside tracked Inspect samples."
                ),
                target="",
                metadata={
                    "schema": "specoracle.terminalbench.inspect_sample.v1",
                    "benchmark": "terminalbench",
                    "dataset_ref": manifest.get("dataset_ref"),
                    "slice": slice_name,
                    "condition": condition,
                    "stable_sample_id": stable_id,
                    "task_id": task_id,
                    "artifact_family": task.get("artifact_family"),
                    "metric_coverage": task.get("metric_coverage"),
                    "manifest_sha256": manifest.get("manifest_sha256"),
                    "summary_row_available": bool(row),
                    "valid_functional_row": row.get("valid_functional_row", ""),
                    "success_bool": row.get("success_bool", ""),
                    "failure_type": row.get("failure_type", ""),
                    "structural_summary_available": row.get("structural_summary_available", ""),
                    "representativeness": (
                        "pinned structurally scorable Python slice, not a "
                        "Terminal-Bench population estimate"
                    ),
                    "raw_content_committed": False,
                    "execution_backend": "harbor",
                    "control_plane": "inspect",
                },
            )
        )
    return MemoryDataset(samples=samples, name=f"terminalbench_{slice_name}_{condition}")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv_like_json(path: Path) -> list[dict[str, str]]:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return []
    import csv

    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _repo_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.exists() or candidate.is_absolute():
        return candidate
    return Path(__file__).resolve().parents[3] / candidate
