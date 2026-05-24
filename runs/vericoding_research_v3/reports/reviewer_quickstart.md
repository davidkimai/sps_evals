# Reviewer Quickstart

This is the fastest self-contained path through the public artifact package.

## Fast Read Path

Read these files in order:

1. [`paper/paper.pdf`](../../../paper/paper.pdf)
2. [`runs/vericoding_research_v3/reports/track3_submission_memo.md`](track3_submission_memo.md)
3. [`runs/vericoding_research_v3/reports/oracle_construction_and_validation.md`](oracle_construction_and_validation.md)
4. [`runs/vericoding_research_v3/reports/final_synthesis.md`](final_synthesis.md)
5. [`runs/vericoding_research_v3/reports/claim_status.json`](claim_status.json)
6. [`runs/vericoding_research_v3/reports/secure_flagship_casebook.md`](secure_flagship_casebook.md)
7. [`runs/vericoding_research_v3/reports/review_boundary_casebook.md`](review_boundary_casebook.md)
8. [`runs/vericoding_research_v3/reports/formal_sidecar_integration_note.md`](formal_sidecar_integration_note.md)
9. [`runs/vericoding_research_v3/reports/verification_facade_dafny_note.md`](verification_facade_dafny_note.md)

This path gives the paper object, hidden-oracle methodology, final claim labels, strongest secure cases, review-boundary examples, the bounded Lean 4 integration frame, and the historical Dafny warning surface.

## Path 1: Audit the Packaged Evidence  
**No API keys required**

From the repository root:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m pytest -q tests/test_vericoding_research_v3.py tests/test_vericoding_schemas.py tests/test_vericoding_secure.py
python scripts/run_vericoding_research_v3.py audit-completion
python scripts/run_vericoding_research_v3.py status
```

Expected verdict:

- `conference_complete=true`
- `final_submit_ready=true`
- `remaining_blockers=[]`
- `Claim A = success`
- `Claim B = partial`
- `Claim C = success`
- `Claim D = success`
- `Claim E = null`

## Path 2: Re-run the Live v3 Workflow  
**API keys required**

If you want to reproduce the live provider-backed workflow, run it in a fresh root:

```bash
mkdir -p runs/reviewer_reruns
scripts/run_with_env.sh python3 scripts/run_vericoding_research_v3.py run-all --root runs/reviewer_reruns/vericoding_research_v3_rerun
scripts/run_with_env.sh python3 scripts/run_vericoding_research_v3.py status --root runs/reviewer_reruns/vericoding_research_v3_rerun
```

If interrupted, resume with:

```bash
scripts/run_with_env.sh python3 scripts/run_vericoding_research_v3.py resume --root runs/reviewer_reruns/vericoding_research_v3_rerun
```

Notes:
- `scripts/run_with_env.sh` sources `~/.zshrc` and requires `OPENAI_API_KEY`.
- The default live model is `gpt-5.4-mini`.
- The packaged artifact is the exact original evidence package; the live rerun is for workflow-level and claim-level reproducibility.

## Short Agent Prompt

```text
Open this repository as a reviewer. Read paper/paper.pdf, runs/vericoding_research_v3/reports/track3_submission_memo.md, runs/vericoding_research_v3/reports/oracle_construction_and_validation.md, and runs/vericoding_research_v3/reports/final_synthesis.md. First audit the packaged artifact with the focused pytest suite, `python scripts/run_vericoding_research_v3.py audit-completion`, and `python scripts/run_vericoding_research_v3.py status`. Report whether the packaged v3 result reproduces and whether Claim A-E in runs/vericoding_research_v3/reports/claim_status.json match the paper. Then, if API keys are available, run the live workflow in a fresh root with `scripts/run_with_env.sh python3 scripts/run_vericoding_research_v3.py run-all --root runs/reviewer_reruns/vericoding_research_v3_rerun`, and report whether the regenerated run is directionally consistent with the packaged claims.
```

## Canonical Evidence

Treat the append-only ledgers as canonical truth:

- [`runs/vericoding_research_v3/ledgers/candidate_bank.jsonl`](../ledgers/candidate_bank.jsonl)
- [`runs/vericoding_research_v3/ledgers/selector_eval.jsonl`](../ledgers/selector_eval.jsonl)
- [`runs/vericoding_research_v3/ledgers/e2e_runs.jsonl`](../ledgers/e2e_runs.jsonl)
- [`runs/vericoding_research_v3/ledgers/secure_eval.jsonl`](../ledgers/secure_eval.jsonl)
- [`runs/vericoding_research_v3/ledgers/triage_decisions.jsonl`](../ledgers/triage_decisions.jsonl)
- [`runs/vericoding_research_v3/ledgers/manual_adjudication.jsonl`](../ledgers/manual_adjudication.jsonl)

Use reports for synthesis and interpretation. Use Inspect logs for runtime provenance, not as the primary analysis database.
