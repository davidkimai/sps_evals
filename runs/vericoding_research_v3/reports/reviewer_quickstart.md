# Reviewer Quickstart

This is the fastest self-contained path through the public artifact package.

## Fast Read Path

Read these files in order:

1. `paper/paper.pdf`
2. `runs/vericoding_research_v3/reports/track3_submission_memo.md`
3. `runs/vericoding_research_v3/reports/oracle_construction_and_validation.md`
4. `runs/vericoding_research_v3/reports/final_synthesis.md`
5. `runs/vericoding_research_v3/reports/claim_status.json`
6. `runs/vericoding_research_v3/reports/secure_flagship_casebook.md`
7. `runs/vericoding_research_v3/reports/review_boundary_casebook.md`
8. `runs/vericoding_research_v3/reports/formal_sidecar_integration_note.md`
9. `runs/vericoding_research_v3/reports/verification_facade_dafny_note.md`

This path gives the paper object, hidden-oracle methodology, final claim labels, strongest secure cases, review-boundary examples, the bounded Lean 4 integration frame, and the historical Dafny warning surface without requiring the broader lineage repository.

## Copy/Paste Terminal Audit

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

## Optional Paper Rebuild

```bash
cd paper
pdflatex -interaction=nonstopmode paper.tex
pdflatex -interaction=nonstopmode paper.tex
qpdf --check paper.pdf
```

This step is optional and only checks that the packaged manuscript rebuilds cleanly.

## Short Agent Prompt

```text
Open this repository as a reviewer. Read paper/paper.pdf, runs/vericoding_research_v3/reports/track3_submission_memo.md, runs/vericoding_research_v3/reports/oracle_construction_and_validation.md, and runs/vericoding_research_v3/reports/final_synthesis.md. Then run the focused pytest suite, `python scripts/run_vericoding_research_v3.py audit-completion`, and `python scripts/run_vericoding_research_v3.py status`. Finally, tell me whether the packaged v3 result reproduces, whether `conference_complete` and `final_submit_ready` are both true, and whether the paper’s Claim A-E labels match runs/vericoding_research_v3/reports/claim_status.json.
```

## Canonical Evidence

Treat the append-only ledgers as canonical truth:

- `runs/vericoding_research_v3/ledgers/candidate_bank.jsonl`
- `runs/vericoding_research_v3/ledgers/selector_eval.jsonl`
- `runs/vericoding_research_v3/ledgers/e2e_runs.jsonl`
- `runs/vericoding_research_v3/ledgers/secure_eval.jsonl`
- `runs/vericoding_research_v3/ledgers/triage_decisions.jsonl`
- `runs/vericoding_research_v3/ledgers/manual_adjudication.jsonl`

Use reports for synthesis and interpretation. Use Inspect logs for runtime provenance, not as the primary analysis database.
