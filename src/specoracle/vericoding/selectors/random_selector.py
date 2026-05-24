from __future__ import annotations

from typing import Any

from specoracle.vericoding.schemas import stable_hash


def select_random(candidates: list[dict[str, Any]], *, task_id: str = "", **_: Any) -> dict[str, Any]:
    if not candidates:
        raise ValueError("candidate pool is empty")
    ordered = sorted(
        candidates,
        key=lambda row: stable_hash({"task_id": task_id, "candidate_id": row["candidate_id"]}),
    )
    return ordered[0]
