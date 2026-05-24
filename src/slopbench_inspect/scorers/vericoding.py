from __future__ import annotations

from typing import Any

from inspect_ai.scorer import CORRECT, INCORRECT, Score, Target, accuracy, scorer
from inspect_ai.solver import TaskState


@scorer(metrics=[accuracy()])
def vericoding_summary_scorer() -> Any:
    """Score sanitized vericoding samples by whether derived evidence exists."""

    async def score(state: TaskState, target: Target) -> Score:
        metadata = state.metadata or {}
        has_evidence = bool(
            int(metadata.get("candidate_summary_rows") or 0)
            and int(metadata.get("selector_summary_rows") or 0)
        )
        return Score(
            value=CORRECT if has_evidence else INCORRECT,
            explanation="derived vericoding summary present" if has_evidence else "missing summary",
            metadata={
                "surface": metadata.get("surface"),
                "split": metadata.get("split"),
                "raw_content_committed": metadata.get("raw_content_committed"),
            },
        )

    return score


@scorer(metrics=[accuracy()])
def vericoding_candidate_support_scorer() -> Any:
    """Score whether a frozen task has claim-bearing candidate support evidence."""

    async def score(state: TaskState, target: Target) -> Score:
        metadata = state.metadata or {}
        candidates = int(metadata.get("candidate_ledger_rows") or 0)
        hidden_support = int(metadata.get("hidden_support_count") or 0)
        secure_support = int(metadata.get("secure_support_count") or 0)
        ok = candidates > 0 and (hidden_support > 0 or secure_support > 0)
        return Score(
            value=CORRECT if ok else INCORRECT,
            explanation="candidate support present" if ok else "candidate support absent",
            metadata=_claim_metadata(metadata),
        )

    return score


@scorer(metrics=[accuracy()])
def vericoding_hidden_disagreement_scorer() -> Any:
    """Score whether visible-vs-hidden disagreement evidence is present."""

    async def score(state: TaskState, target: Target) -> Score:
        metadata = state.metadata or {}
        ok = int(metadata.get("visible_hidden_fail_count") or 0) > 0
        return Score(
            value=CORRECT if ok else INCORRECT,
            explanation="visible-pass hidden-fail evidence present" if ok else "no visible-pass hidden-fail evidence",
            metadata=_claim_metadata(metadata),
        )

    return score


@scorer(metrics=[accuracy()])
def vericoding_secure_false_accept_scorer() -> Any:
    """Score whether secure challenge false-accept opportunities exist."""

    async def score(state: TaskState, target: Target) -> Score:
        metadata = state.metadata or {}
        ok = int(metadata.get("secure_false_accept_candidate_count") or 0) > 0
        return Score(
            value=CORRECT if ok else INCORRECT,
            explanation="secure false-accept opportunity present" if ok else "no secure false-accept opportunity",
            metadata=_claim_metadata(metadata),
        )

    return score


@scorer(metrics=[accuracy()])
def vericoding_runtime_log_scorer() -> Any:
    """Score whether the task has corresponding paper-analysis ledger rows."""

    async def score(state: TaskState, target: Target) -> Score:
        metadata = state.metadata or {}
        source = str(metadata.get("inspect_source") or "")
        if source == "external_guardrail":
            ok = int(metadata.get("external_ledger_rows") or 0) > 0
        elif source == "formal_overlay":
            ok = int(metadata.get("formal_ledger_rows") or 0) > 0
        else:
            ok = int(metadata.get("candidate_ledger_rows") or 0) > 0
        return Score(
            value=CORRECT if ok else INCORRECT,
            explanation="ledger-backed runtime sample" if ok else "missing ledger-backed runtime sample",
            metadata=_claim_metadata(metadata),
        )

    return score


@scorer(metrics=[accuracy()])
def vericoding_trust_boundary_scorer() -> Any:
    """Score whether a sample carries concrete ship/no-ship/review boundary metadata."""

    async def score(state: TaskState, target: Target) -> Score:
        metadata = state.metadata or {}
        ok = bool(
            metadata.get("narrow_waist")
            and metadata.get("spec_coherent")
            and metadata.get("review_boundary_clear")
            and metadata.get("accepted_decision")
            and metadata.get("rejected_decision")
            and metadata.get("human_review_required")
        )
        return Score(
            value=CORRECT if ok else INCORRECT,
            explanation="trust-boundary metadata present" if ok else "missing trust-boundary metadata",
            metadata=_claim_metadata(metadata),
        )

    return score


def _claim_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "surface": metadata.get("surface"),
        "split": metadata.get("split"),
        "task_id": metadata.get("task_id"),
        "stable_sample_id": metadata.get("stable_sample_id"),
        "inspect_source": metadata.get("inspect_source"),
        "basin": metadata.get("basin"),
        "secure_challenge": metadata.get("secure_challenge"),
        "candidate_ledger_rows": metadata.get("candidate_ledger_rows"),
        "selector_ledger_rows": metadata.get("selector_ledger_rows"),
        "e2e_ledger_rows": metadata.get("e2e_ledger_rows"),
        "hidden_support_count": metadata.get("hidden_support_count"),
        "visible_hidden_fail_count": metadata.get("visible_hidden_fail_count"),
        "secure_false_accept_candidate_count": metadata.get("secure_false_accept_candidate_count"),
        "raw_content_committed": metadata.get("raw_content_committed"),
        "narrow_waist": metadata.get("narrow_waist"),
        "review_boundary_clear": metadata.get("review_boundary_clear"),
        "support_status": metadata.get("support_status"),
        "secure_challenge_eligible": metadata.get("secure_challenge_eligible"),
    }
