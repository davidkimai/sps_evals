from __future__ import annotations

from typing import Any

from specoracle.vericoding.selection_features import candidate_feature_score


def select_with_llm_judge(candidates: list[dict[str, Any]], **_: Any) -> dict[str, Any]:
    """Deterministic local proxy for a schema-constrained judge in v1.

    The prompt version and cost fields are tracked in selector ledgers. Paid
    provider calls can replace this function without changing ledger schemas.
    """
    if not candidates:
        raise ValueError("candidate pool is empty")
    return sorted(
        candidates,
        key=lambda row: (
            -candidate_feature_score(row),
            str(row["candidate_id"]),
        ),
    )[0]
