# Claim Map

## Claim A: Hidden Evaluators Are Necessary

Status: success.

Evidence:

- 16 confirmatory visible-pass / hidden-fail tasks.
- 8 secure visible-pass / hidden-secure-fail tasks.

Interpretation: visible tests are not a sufficient acceptance proxy.

## Claim B: Ranking Is Support-Conditioned

Status: partial.

Evidence:

- 8 support-present tasks observed in the claim registry.
- 9 support-absent tasks observed in the claim registry.
- specoracle-or-LLM selection beats tests-only on 2 tasks.

Interpretation: selection helps only after candidate generation creates hidden-correct support. The internal support attack wave is a mechanism result, not a failure of the project.

## Claim C: Secure Rejection Oracle Value

Status: success.

Evidence:

- tests-only secure false accept on 7 tasks.
- specoracle secure false accept on 1 task.
- secure false accept reduced on 6 tasks.

Interpretation: hidden executable specs provide no-ship value, not only ranking value.

## Claim D: Review-Boundary Necessity

Status: success.

Evidence:

- 6 escalate-to-review decisions.
- review-boundary cases span authorization and parser families.

Interpretation: passing visible and hidden executable checks still does not eliminate all human review surfaces.

## Claim E: Bounded Repair

Status: null.

Evidence:

- equal-cost repair wins: 0.

Interpretation: repair is not a universal escape hatch. It should remain a bounded negative result.
