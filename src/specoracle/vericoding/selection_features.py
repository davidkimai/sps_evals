from __future__ import annotations

from typing import Any


def candidate_feature_score(row: dict[str, Any]) -> float:
    """Observable feature score used before selector-specific policy."""
    score = 0.0
    if row.get("visible_compile_pass"):
        score += 1.0
    if row.get("visible_tests_pass"):
        score += 2.0
    if row.get("visible_proxy_checks_pass"):
        score += 0.8
    if row.get("visible_regression_proxy_pass"):
        score += 0.6
    if row.get("visible_security_proxy_pass"):
        score += 0.6
    if row.get("parse_ok"):
        score += 0.5
    cc = row.get("cc_average")
    if isinstance(cc, int | float):
        score += max(0.0, 1.0 - (float(cc) / 12.0))
    redundancy = row.get("redundancy_score")
    if isinstance(redundancy, int | float):
        score += max(0.0, 0.5 - float(redundancy))
    return round(score, 6)


def hard_filter_passes(row: dict[str, Any]) -> bool:
    return bool(row.get("parse_ok") and row.get("visible_compile_pass"))
