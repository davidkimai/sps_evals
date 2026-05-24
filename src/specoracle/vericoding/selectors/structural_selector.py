from __future__ import annotations

from typing import Any


def select_with_structural(candidates: list[dict[str, Any]], **_: Any) -> dict[str, Any]:
    if not candidates:
        raise ValueError("candidate pool is empty")
    viable = [row for row in candidates if row.get("parse_ok")] or candidates
    return sorted(
        viable,
        key=lambda row: (
            float(row.get("cc_average") or 999),
            int(row.get("max_nesting_depth") or 999),
            -(float(row.get("maintainability_index") or 0)),
            float(row.get("redundancy_score") or 999),
            str(row["candidate_id"]),
        ),
    )[0]
