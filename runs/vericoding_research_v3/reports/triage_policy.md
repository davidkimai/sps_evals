# Triage Policy

Created: 2026-05-19T08:42:51Z

This policy applies to selected final artifacts.

## auto_accept

Visible evaluator passes, hidden evaluator passes, no secure/regression blocker, and no unresolved high-severity review-boundary blocker.

## auto_reject

Parse failure, runtime failure, visible failure, hidden executable failure, secure false-accept condition, or regression blocker.

## escalate_to_review

Executable checks pass but material ambiguity remains: unclear spec intent, wrapper/runtime/TCB dependency, assumption gap, high review burden, or formal/review-boundary concern.
