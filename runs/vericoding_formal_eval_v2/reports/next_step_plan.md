# Next Step Plan

## Current judgment

`vericoding_formal_eval_v2` is a real bounded formal-sidecar success on Claims A/B/C.

Current status:
- Claim A: success
- Claim B: success
- Claim C: success
- Claim D: unsupported

Headline metrics:
- visible-formal-fail tasks: `5`
- support-present tasks: `5`
- support-absent tasks: `1`
- tests-only false-accept tasks: `3`
- formal false-accept tasks: `0`
- review escalations: `0`

## What not to do

- Do not expand task count.
- Do not turn the sidecar into the new project center.
- Do not reopen broad formal-methods scope.

## Only justified next move

If we continue, the only high-value follow-up is a **review-boundary attack wave** targeting:
- `timing_safe_compare`
- `safe_path_validation`

Goal:
- produce at least one candidate with:
  - `formal_pass = true`
  - `review_required = true`

That would turn Claim D from unsupported into real bounded evidence.

## Suggested new prompt families

- `readability_minimal_prompt`
- `stdlib_wrapper_prompt`

These should be added as narrow extra families, not replacements.

## Stop rule

If a targeted v2.2 review-boundary wave still produces zero escalations, stop and keep v2 as the final bounded formal-sidecar artifact.
