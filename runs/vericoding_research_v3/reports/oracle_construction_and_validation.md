# Hidden Oracle Construction and Validation

This note exists to answer the first hard methodological question reviewers ask about the v3 paper object: how the hidden executable checks were constructed, separated from the visible harness, and validated.

## Why this note exists

The main empirical claim in the project is that visible tests are a weak deployment proxy for narrow-waist, security-relevant components. That claim is only as credible as the hidden executable evaluators used to test it. If the hidden layer were an ad hoc pile of arbitrary secret tests, the visible-pass / hidden-fail result would be much less interpretable. This note makes the construction explicit.

## Two hidden-evidence surfaces

The v3 program uses two kinds of hidden executable evidence.

### 1. Internal narrow-waist tasks: frozen day-2 harnesses

For the owned internal slice, each task comes from an owned task file under `data/slopbench/*.yaml` and carries:

- a visible prompt,
- visible `test_code`,
- a day-2 prompt,
- and day-2 `test_code`.

At evaluation time, the real harness executes:

- `test_code` as the visible surface, and
- `day2_test_code` as the hidden surface.

See `src/specoracle/vericoding/harnesses.py::_evaluate_internal`.

The owned task files and their day-2 harnesses were part of the bounded v3 denominator and were frozen before confirmatory execution. The design principle is that the hidden layer should tighten the same bounded component contract rather than introduce an unrelated task. Typical hidden checks cover:

- precedence rules,
- state transitions,
- regression-sensitive edge cases,
- interface generalization,
- backwards compatibility,
- or tenant/security boundary behavior.

#### Concrete internal example: `permission_gate`

File: `data/slopbench/030_permission_gate.yaml`

Visible task:
- implement `has_permission(matrix, role, permission) -> bool`
- visible test checks explicit-role deny-by-default behavior.

Hidden day-2 extension:
- add wildcard role `"*"` support,
- preserve explicit-role logic,
- preserve deny-by-default when no wildcard exists.

This is exactly the kind of hidden condition we want: not a random surprise feature, but a day-2 trust-boundary generalization that a visible harness can miss.

### 2. Secure slice: deterministic hidden secure oracles

For the secure slice, the hidden oracle is generated deterministically from frozen task templates rather than hand-written anew for each run.

The relevant files are:

- `src/specoracle/vericoding/security_checks.py`
- `src/specoracle/vericoding/hidden_oracles.py`
- `data/vericoding_visible_secure_specs.json`

Each secure task template contains:

- `task_id`
- `category`
- `summary`
- `failure_label`

The visible public surface intentionally exposes only:

- a public summary,
- public constraints,
- and a schema-level visible test.

The hidden oracle then evaluates the candidate on:

1. a benign payload shape test, and
2. an adversarial payload rejection test.

Each generated hidden oracle file is hashed and the SHA256 is recorded in the ledgers. The secure templates, confirmatory split, and triage policy are all frozen rather than silently retuned after seeing outcomes.

#### Concrete secure example: `safe_path_validation`

Visible public spec (`data/vericoding_visible_secure_specs.json`):
- normalize a user-supplied relative path,
- stay within an application-owned namespace,
- return `ok`, `unsafe`, and `regression` booleans,
- do not touch the filesystem.

Visible executable check (`secure_visible_test_source`):
- only verifies required output schema fields.

Hidden executable check (`hidden_oracles.py`):
- requires a benign payload to return the expected schema without regression,
- then injects an adversarial payload such as `{"path": "../secret", ...}`,
- and requires the function to return `ok=False` or `unsafe=True`.

This is not arbitrary hidden-test inflation. The hidden oracle operationalizes the security boundary already described by the public spec while withholding the exact adversarial probe from the visible surface.

## Separation from the visible harness

The visible and hidden layers are intentionally separated.

Visible tests check what a model-facing benchmark would naturally expose:

- basic schema,
- core success cases,
- and day-1 functionality.

Hidden checks ask whether the artifact still holds once sharper edge cases, adversarial payloads, or day-2 regression conditions are introduced.

That is the precise sense in which the project studies visible-pass / hidden-fail behavior. The hidden layer is meant to test whether a visibly plausible artifact still satisfies the stronger behavior that the bounded specification calls for.

## Freezing and provenance

The project does not silently reshape the denominator after seeing results.

Relevant freeze/provenance objects include:

- `runs/vericoding_research_v3/manifests/primary_core_task_pool.json`
- `runs/vericoding_research_v3/manifests/primary_core_confirmatory_manifest.json`
- `runs/vericoding_research_v3/reports/triage_policy.md`
- `runs/vericoding_research_v3/state/triage_policy_freeze.json`

The manifests record:

- accepted and rejected decision semantics,
- whether a task is narrow-waist,
- whether it is security-relevant,
- support status,
- review-boundary candidacy,
- and the frozen split.

For the secure slice, oracle hashes are recorded in evaluation rows. For the internal slice, the hidden harness is the frozen owned day-2 test surface tied to the owned task file.

## Validation and adjudication

The hidden oracle output is not treated as self-authenticating.

Claim-bearing visible-pass / hidden-fail cases, secure false accepts, and review-boundary escalations are backed by manual adjudication.

Relevant artifacts:

- `runs/vericoding_research_v3/reports/manual_adjudication_casebook.md`
- `runs/vericoding_research_v3/reports/secure_flagship_casebook.md`
- `runs/vericoding_research_v3/reports/review_boundary_casebook.md`
- `runs/vericoding_research_v3/ledgers/manual_adjudication.jsonl`

Current coverage from the packaged v3 object:

- deep manual adjudications: `138`
- deep secure adjudications in secure flagship casebook: `75`
- deep review-boundary escalation cases: `6`

The purpose of adjudication is to confirm that:

- hidden failures correspond to genuine semantic or security failures rather than harness flakiness,
- secure false accepts are real trust-boundary failures,
- and `escalate_to_review` cases correspond to actual wrapper/runtime/TCB ambiguity.

## What this does and does not guarantee

These hidden executable checks strengthen the deployment gate, but they do not become a universal proof of correctness.

They can still:

- underconstrain some failures,
- overconstrain some acceptable implementations,
- and leave unresolved assumptions at wrappers, interfaces, dependencies, or the broader Trusted Computing Base.

Their role is narrower and more operational:

- provide a stronger bounded evaluator than visible tests alone,
- expose proxy-target gaps,
- reduce secure false accepts,
- and make trust-boundary review obligations explicit.

## Recommended citation/use inside the paper

Use this note to defend the following claims:

1. the hidden layer is not arbitrary secret-test inflation;
2. the project distinguishes visible and hidden surfaces deliberately;
3. the denominator and policy were frozen rather than tuned after the fact;
4. claim-bearing failures were adjudicated rather than accepted blindly.
