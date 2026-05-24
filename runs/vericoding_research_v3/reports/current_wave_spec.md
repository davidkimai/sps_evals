# Current Wave Spec: claim_hardening_adjudication_wave_1

- Objective: Harden secure flagship, auto-accept, and review-boundary cases that were under-covered by the first adjudication wave.
- Surfaces: `secure_flagship, auto_accept, escalate_to_review`
- Success condition: Claim C, auto-accept, and escalation cases all have deep ledger-backed adjudication coverage.
- Demotion condition: Any case type with no material rows is explicitly excluded from flagship use.

## Expected Outputs

- `ledgers/manual_adjudication.jsonl`
- `reports/adjudication_coverage_audit.md`
- `reports/secure_flagship_casebook.md`
- `reports/review_boundary_casebook.md`
