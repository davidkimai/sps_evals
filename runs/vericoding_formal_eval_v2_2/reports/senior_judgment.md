# Senior Judgment

## Verdict

`vericoding_formal_eval_v2_2` succeeded at the only strategically justified follow-up objective after `formal_eval_v2`:

- produce at least one **formal-pass / review-required** candidate on a narrow, honest, trust-boundary-relevant slice.

That objective is now met.

## What this wave adds beyond v2

`formal_eval_v2` already established:
- visible-pass / formal-fail behavior,
- support-conditioned ranking,
- false-accept reduction on the bounded formal slice.

`formal_eval_v2_2` adds the missing review-boundary result:
- bounded formal evidence can still leave unresolved trust-boundary questions,
- and the correct operational action is **`escalate_to_review`**, not automatic authorization.

The strongest confirmatory example is:
- `timing_safe_compare:gpt-5.4-mini:behavioral_minimal_prompt:formal:0`
- selected by `tests_only_selector`
- `formal_pass = true`
- `decision = escalate_to_review`

This is exactly the phenomenon we wanted:
- the candidate satisfies bounded visible and formal I/O checks,
- but still does not discharge the constant-time trust boundary,
- so human review remains necessary.

## How to use this result

Use `formal_eval_v2_2` as a **bounded secondary proof-point** for the main Track 3 project.

Appropriate claim:
- executable trust-boundary gates can combine visible checks, bounded formal evidence, and explicit review boundaries rather than forcing a brittle accept/reject binary.

Inappropriate claim:
- broad formal verification is now the center of the project,
- or this tiny attack wave replaces the larger v3 trust-boundary denominator.

## Stop rule

No broader formal expansion is currently justified.

Recommended stopping point:
- keep `formal_eval_v2` as the main bounded formal-sidecar slice for A/B/C,
- keep `formal_eval_v2_2` as the targeted review-boundary wave for D,
- do not broaden task count or formal-methods scope unless a new paper need clearly appears.
