from __future__ import annotations

from typing import Any

from specoracle.vericoding.selection_features import candidate_feature_score, hard_filter_passes


def select_with_specoracle(candidates: list[dict[str, Any]], **_: Any) -> dict[str, Any]:
    """Select a candidate through hard-filter, feature score, shortlist, compare."""
    if not candidates:
        raise ValueError("candidate pool is empty")
    filtered = [row for row in candidates if hard_filter_passes(row)] or candidates
    shortlist = sorted(
        filtered,
        key=lambda row: (-candidate_feature_score(row), str(row["candidate_id"])),
    )[:4]
    return sorted(
        shortlist,
        key=lambda row: (
            -_spec_conditioned_score(row),
            str(row["candidate_id"]),
        ),
    )[0]


def _spec_conditioned_score(row: dict[str, Any]) -> float:
    score = candidate_feature_score(row)
    if row.get("candidate_source_type") == "live_model":
        score += 0.2
    if str(row.get("candidate_source", "")).startswith("spec"):
        score += 0.2
    return score
