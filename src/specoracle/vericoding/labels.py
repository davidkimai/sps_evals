from __future__ import annotations

from typing import Any

from specoracle.vericoding.schemas import CandidateLabel


def derive_candidate_label(row: dict[str, Any]) -> CandidateLabel:
    if not row.get("parse_ok") or not row.get("visible_compile_pass"):
        return "syntax_fail"
    if row.get("insecure_candidate") or not row.get("security_checks_pass", True):
        return "security_fail"
    if row.get("regression_candidate") or not row.get("regression_checks_pass", True):
        return "regression_fail"
    if row.get("hidden_tests_pass") and row.get("property_checks_pass", True):
        return "correct"
    if row.get("visible_tests_pass"):
        return "plausible_wrong"
    return "runtime_fail"


def label_rank(label: str) -> int:
    ranks = {
        "correct": 6,
        "plausible_wrong": 3,
        "regression_fail": 2,
        "security_fail": 1,
        "runtime_fail": 0,
        "syntax_fail": -1,
        "infra_fail": -2,
    }
    return ranks.get(label, -3)
