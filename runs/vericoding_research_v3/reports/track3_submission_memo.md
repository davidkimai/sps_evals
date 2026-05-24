# Track 3 Submission Memo

## Submission Object

This project is a prototype verification layer for AI-written software. It evaluates autonomous coding outputs with visible tests, hidden executable evaluators, secure/regression checks, and review-boundary rules, then emits one of three decisions: `auto_accept`, `auto_reject`, or `escalate_to_review`.

## Why It Fits Track 3

Track 3 asks for spec-as-evaluator workflows: candidate generation, specification-driven discrimination, semantic regression catching, and credible paths toward high-assurance code acceptance. V3 implements exactly that pattern on a bounded owned suite.

## Main Evidence

- 24-task primary core, with 8 dev and 16 confirmatory tasks.
- 24-task expansion suite for mechanism and review-boundary stress.
- 1405 claim-bearing candidate rows.
- 360 selector rows.
- 360 E2E rows.
- 369 secure-eval rows.
- 72 triage decisions.
- 138 deep manual adjudication rows.

## Claim Snapshot

- Claim A: success. Visible tests are insufficient.
- Claim B: partial. Ranking is support-conditioned, and internal support generation remains hard.
- Claim C: success. Spec-aware checks reduce secure false accepts.
- Claim D: success. Some executable-pass artifacts still need review escalation.
- Claim E: null. Repair does not beat equal-cost fresh generation here.

## Reviewer Reading Path

1. `runs/vericoding_research_v3/PRIMARY_CLAIM_LOCK.md`
2. `runs/vericoding_research_v3/reports/final_synthesis.md`
3. `runs/vericoding_research_v3/reports/claim_status.json`
4. `runs/vericoding_research_v3/reports/secure_flagship_casebook.md`
5. `runs/vericoding_research_v3/reports/review_boundary_casebook.md`
6. `runs/vericoding_research_v3/reports/formal_sidecar_integration_note.md`
7. `paper/paper.tex`

## Non-Claims

The project does not claim universal program synthesis, production readiness, formal proof of the full system, or strong external portability. External and SCBench surfaces are explicitly demoted unless treated as tertiary context. Dafny is not a new center of gravity.
