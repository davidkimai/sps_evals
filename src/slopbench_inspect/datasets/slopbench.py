from __future__ import annotations

from pathlib import Path
from typing import Iterable

from inspect_ai.dataset import MemoryDataset, Sample

from specoracle.cli import load_tasks
from specoracle.config import GENERATION_USER_TEMPLATE


def load_slopbench_samples(
    dataset_dir: str | Path = "data/slopbench_min",
    *,
    task_ids: Iterable[str] | None = None,
    limit: int | None = None,
) -> MemoryDataset:
    """Load SlopBench YAML tasks into Inspect ``Sample`` objects."""
    dataset_path = _repo_path(dataset_dir)
    wanted = set(task_ids or [])
    samples: list[Sample] = []
    for task in load_tasks(dataset_path):
        if wanted and task.id not in wanted:
            continue
        samples.append(
            Sample(
                id=task.id,
                input=GENERATION_USER_TEMPLATE.format(
                    task_id=task.id,
                    entry_point=task.entry_point,
                    prompt=task.prompt,
                ),
                target="",
                metadata={
                    "benchmark": "slopbench",
                    "task_id": task.id,
                    "entry_point": task.entry_point,
                    "tags": list(task.tags),
                    "test_code": task.test_code,
                    "human_reference": task.human_reference,
                    "mock_solution": task.mock_solution,
                },
            )
        )
        if limit is not None and len(samples) >= limit:
            break
    return MemoryDataset(samples=samples, name="slopbench")


def _repo_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.exists():
        return candidate
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / candidate
