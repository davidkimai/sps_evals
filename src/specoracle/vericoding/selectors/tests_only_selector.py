from __future__ import annotations

from typing import Any


def select_with_tests_only(candidates: list[dict[str, Any]], **_: Any) -> dict[str, Any]:
    if not candidates:
        raise ValueError("candidate pool is empty")
    return sorted(
        candidates,
        key=lambda row: (
            not bool(row.get("visible_tests_pass")),
            not bool(row.get("visible_compile_pass")),
            str(row["candidate_id"]),
        ),
    )[0]
