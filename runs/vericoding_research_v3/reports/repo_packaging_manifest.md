# Repo Packaging Manifest

This manifest describes the curated Track 3 v3 package staged from the clean packaging worktree. The package is designed to be reviewable without importing raw runtime debris or unrelated predecessor sprawl.

## Primary Claim-Bearing Files

The v3 claim-bearing package is centered on:

- `runs/vericoding_research_v3/ledgers/`
- `runs/vericoding_research_v3/metrics/`
- `runs/vericoding_research_v3/manifests/`
- `runs/vericoding_research_v3/config/`
- `runs/vericoding_research_v3/state/`
- `runs/vericoding_research_v3/reports/`
- `runs/vericoding_research_v3/paper_artifacts/tables/`
- `runs/vericoding_research_v3/paper_artifacts/appendix_cases/`
- `runs/vericoding_research_v3/inspect_logs/`
- curated summaries under `runs/vericoding_research_v3/data/wrangled/`
- curated provenance notes under `runs/vericoding_research_v3/provenance/`

The main code and test surface is:

- `README.md`
- `paper/paper.tex`
- `paper/paper.pdf`
- `scripts/run_vericoding_research_v3.py`
- `scripts/run_with_env.sh`
- `data/vericoding_visible_secure_specs.json`
- `src/slopbench_inspect/`
- `src/specoracle/vericoding/live_generation.py`
- `src/specoracle/vericoding/live_selection.py`
- `src/specoracle/vericoding/research_program_v3.py`
- `src/specoracle/vericoding/schemas.py`
- `tests/test_vericoding_research_v3.py`

## Secondary Contextual Files

The package retains selected prior-work context:

- Sprint 9 SCBench contextual summaries and failure analysis
- Sprint 10 Terminal-Bench contextual summaries, manifests, and failure analysis
- selected v2 oracle/hybrid lineage reports and paper tables

These files are context, not replacements for v3 claim-bearing evidence.

## Quarantined Directories

The following directories are intentionally preserved outside the clean package or ignored by the packaging branch:

- `runs/vericoding_research_v3/raw_jobs/`
- `runs/vericoding_research_v3/provenance/reading_cache/`
- `runs/vericoding_research_v3/data/wrangled/live_candidates/`
- `runs/vericoding_research_v3/data/wrangled/repairs/`
- `runs/sprint10_closeout_v1/raw_jobs/`
- `runs/vericoding_research_v2/raw_jobs/`
- `runs/vericoding_research_v2/inspect_logs/`
- `runs/vericoding_research_v2/data/wrangled/secure_challenge_candidates/`

Bulk regenerated v2 ledgers, metrics, wrangled outputs, and stale v2 readiness reports are also excluded unless explicitly listed in the prior-work crosswalk.

## Canonical Truth Files

Append-only ledgers are canonical for analysis. Inspect logs are runtime provenance. Reports, tables, and package summaries are derived outputs.

The key readiness and state files are:

- `runs/vericoding_research_v3/state/completion_contract.json`
- `runs/vericoding_research_v3/state/final_submit_readiness.json`
- `runs/vericoding_research_v3/state/program_state.json`
- `runs/vericoding_research_v3/state/active_blockers.json`
- `runs/vericoding_research_v3/reports/claim_status.json`
- `runs/vericoding_research_v3/reports/final_synthesis.md`
- `runs/vericoding_research_v3/reports/final_senior_audit.md`
- `runs/vericoding_research_v3/reports/final_readiness_report.md`
- `runs/vericoding_research_v3/reports/track3_alignment_doctrine.md`
- `runs/vericoding_research_v3/reports/track3_submission_memo.md`
- `runs/vericoding_research_v3/reports/reviewer_quickstart.md`
- `runs/vericoding_research_v3/reports/dafny_sidecar_decision.md`

## Reproduce And Audit Commands

From the package worktree:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python3 scripts/run_vericoding_research_v3.py audit-completion
python3 scripts/run_vericoding_research_v3.py status
pytest -q tests/test_vericoding_research_v3.py
```

The source-shell wrapper for live provider-backed or Harbor-backed runs is:

```bash
scripts/run_with_env.sh <command> [args...]
```

## Packaging Policy

This commit should read as a v3 package plus selected lineage, not a kitchen-sink import. If a file is not needed for the v3 paper object, reviewer audit, canonical ledgers, or explicitly demoted contextual lineage, it should stay out of the staged package.
