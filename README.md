# SPS Evals

**SPS Evals** is the public, reviewer-facing artifact package for **The Illusion of Passing Tests** and its Secure Program Synthesis (SPS) evaluation program.

This repository is intentionally scoped around the **paper-owned denominator**:
- the v3 executable trust-boundary study,
- the bounded Lean 4 formal follow-up surfaces cited in the paper,
- and the historical Dafny verification-façade warning surface.

It is meant to let a reviewer read the paper, inspect the claim-bearing evidence, and rerun the core audit **without needing the broader exploratory lineage repo**.

## Prior-Work Disclosure

This package builds on earlier exploratory work in [SpecOracle](https://github.com/davidkimai/specoracle), but the **claim-bearing denominator under review here** is the frozen v3 trust-boundary study packaged in this repository.

## If You Only Have Five Minutes

Start here:

1. `paper/paper.pdf`
2. `runs/vericoding_research_v3/reports/reviewer_quickstart.md`
3. `runs/vericoding_research_v3/reports/track3_submission_memo.md`
4. `runs/vericoding_research_v3/reports/oracle_construction_and_validation.md`
5. `runs/vericoding_research_v3/reports/final_synthesis.md`
6. `runs/vericoding_research_v3/reports/claim_status.json`

## Main Scientific Object

The main scientific object is the v3 trust-boundary program under:
- `runs/vericoding_research_v3/`

Headline claim labels:

| Claim | Status | Reading |
|---|---:|---|
| A | success | Visible tests are insufficient acceptance proxies. |
| B | partial | Ranking helps only when evaluator-passing support exists. |
| C | success | Hidden executable checks reduce secure false accepts. |
| D | success | Some executable-pass artifacts still require review escalation. |
| E | null | Repair does not beat equal-cost fresh generation here. |

## Secondary Formal Evidence

The paper also cites two bounded Lean 4 formal-evaluator surfaces and one historical Dafny warning surface:

- `runs/vericoding_formal_eval_v2/`
- `runs/vericoding_formal_eval_v2_2/`
- `runs/dafny_full_claude/`
- `runs/vericoding_research_v3/reports/verification_facade_dafny_note.md`

Use these as bounded supporting evidence for review boundaries and formal-evidence interpretation, not as the paper's primary denominator.

## Copy/Paste Terminal Audit

From a fresh machine or clean shell, the fastest reproducibility path is:

```bash
git clone https://github.com/davidkimai/sps_evals.git
cd sps_evals
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m pytest -q tests/test_vericoding_research_v3.py tests/test_vericoding_schemas.py tests/test_vericoding_secure.py
python scripts/run_vericoding_research_v3.py audit-completion
python scripts/run_vericoding_research_v3.py status
```

Expected v3 verdict:
- `conference_complete=true`
- `final_submit_ready=true`
- `remaining_blockers=[]`

Expected headline claim labels in `runs/vericoding_research_v3/reports/claim_status.json`:
- `Claim A = success`
- `Claim B = partial`
- `Claim C = success`
- `Claim D = success`
- `Claim E = null`

## Optional Paper Rebuild

If you want to rebuild the manuscript locally:

```bash
cd paper
pdflatex -interaction=nonstopmode paper.tex
pdflatex -interaction=nonstopmode paper.tex
qpdf --check paper.pdf
```

This step is optional and requires a local LaTeX installation plus `qpdf`.

## Short Agent Prompt

If you prefer to use an agent instead of manually running the commands above, paste this:

```text
Open this repository as a reviewer. Read README.md, paper/paper.tex (or paper/paper.pdf), and runs/vericoding_research_v3/reports/reviewer_quickstart.md. Then run the focused pytest suite, `python scripts/run_vericoding_research_v3.py audit-completion`, and `python scripts/run_vericoding_research_v3.py status`. Finally, report whether (1) the packaged v3 result reproduces, (2) `conference_complete` and `final_submit_ready` are both true, and (3) the claim labels in runs/vericoding_research_v3/reports/claim_status.json match the paper.
```

## Canonical Evidence

For the main study, treat the append-only ledgers as canonical truth:

- `runs/vericoding_research_v3/ledgers/candidate_bank.jsonl`
- `runs/vericoding_research_v3/ledgers/selector_eval.jsonl`
- `runs/vericoding_research_v3/ledgers/e2e_runs.jsonl`
- `runs/vericoding_research_v3/ledgers/secure_eval.jsonl`
- `runs/vericoding_research_v3/ledgers/triage_decisions.jsonl`
- `runs/vericoding_research_v3/ledgers/manual_adjudication.jsonl`

Inspect logs are packaged as runtime provenance, not as the primary analysis database.

## Public Repo Layout

- `paper/` — canonical manuscript source and PDF
- `runs/vericoding_research_v3/` — main claim-bearing evidence package
- `runs/vericoding_formal_eval_v2/` — bounded Lean 4 formal-evaluator slice
- `runs/vericoding_formal_eval_v2_2/` — targeted Lean 4 review-boundary follow-up
- `runs/dafny_full_claude/` — historical Dafny evidence cited in the paper
- `src/` — evaluation/runtime code
- `data/` — frozen task/spec surfaces
- `formal/` — Lean 4 formal harness source
- `scripts/` — top-level audit/run entrypoints
- `tests/` — focused audit-oriented test subset

## Running Provider-Backed Commands

If you want to run provider-backed commands, use the sourced-shell wrappers so API keys and toolchain variables come from your shell environment:

```bash
scripts/run_with_env.sh python3 scripts/run_vericoding_research_v3.py status
scripts/run_with_env_formal.sh python3 scripts/run_vericoding_formal_eval_v2_2.py status
```

## License

MIT
