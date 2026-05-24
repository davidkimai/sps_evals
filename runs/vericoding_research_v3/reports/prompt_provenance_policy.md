# Prompt Provenance Policy

Created: 2026-05-19T06:57:18Z

Claim-bearing prompts may use only visible primary manifests, visible task-spec sources, and frozen public constraints.

## Forbidden Source Files

- `src/specoracle/vericoding/hidden_oracles.py`
- `src/specoracle/vericoding/harnesses.py` hidden-harness internals
- generated hidden oracle files under `artifacts/*hidden_oracles*`
- hidden test files or hidden evaluator logic
- post-failure adjudication casebooks and review notes

## Prompt Provenance Matrix

| Surface | Allowed prompt sources | Forbidden prompt sources |
|---|---|---|
| internal | `data/slopbench/*.yaml` visible task prompt/spec fields; frozen manifests | hidden/day2 test code, hidden evaluator output |
| secure | `data/vericoding_visible_secure_specs.json`; frozen manifests | `hidden_oracles.py`, generated hidden oracle tests, adversarial payload tests |
| expansion | visible expansion manifest fields; visible spec files | hidden evaluator code, review notes after failures |
| external/transfer | sanitized public metadata and integration docs | private benchmark artifacts or hidden tests |
