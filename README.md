# SPS Evals

**SPS Evals** is the public artifact package for **The Illusion of Passing Tests**, a Secure Program Synthesis (SPS) project about **verifying what AI is writing before it crosses a trust boundary**.

The core object in this repository is a **spec-as-evaluator** workflow: generate candidate implementations, evaluate them with visible tests and stronger hidden executable checks, and then make a deployment decision — `auto_accept`, `auto_reject`, or `escalate_to_review`.

This repository is intentionally scoped around the paper’s main evidence package:
- the **v3 trust-boundary study**,
- the **bounded Lean 4 formal follow-up surfaces** cited in the paper,
- and the **historical Dafny verification-façade warning** discussed as secondary evidence.

In other words: this repo is for reading the paper, auditing the packaged evidence, and, if desired, re-running the live evaluation workflow in a fresh root.

## Prior Work Disclosure

This package grows out of earlier exploratory work in [SpecOracle](https://github.com/davidkimai/specoracle), but the **main object under review here** is the frozen **v3 trust-boundary study** packaged in this repository.

## If You Only Have Five Minutes

Start here:

1. [`paper/paper.pdf`](paper/paper.pdf)
2. [`runs/vericoding_research_v3/reports/reviewer_quickstart.md`](runs/vericoding_research_v3/reports/reviewer_quickstart.md)
3. [`runs/vericoding_research_v3/reports/track3_submission_memo.md`](runs/vericoding_research_v3/reports/track3_submission_memo.md)
4. [`runs/vericoding_research_v3/reports/oracle_construction_and_validation.md`](runs/vericoding_research_v3/reports/oracle_construction_and_validation.md)
5. [`runs/vericoding_research_v3/reports/final_synthesis.md`](runs/vericoding_research_v3/reports/final_synthesis.md)
6. [`runs/vericoding_research_v3/reports/claim_status.json`](runs/vericoding_research_v3/reports/claim_status.json)

## Main Scientific Object

The main scientific object is the packaged v3 study in [`runs/vericoding_research_v3/`](runs/vericoding_research_v3/).

Headline claim labels:

| Claim | Status | Reading |
|---|---:|---|
| A | success | Visible tests are weak deployment proxies. |
| B | partial | Ranking helps only when hidden-correct support exists in the candidate pool. |
| C | success | Hidden executable checks reduce secure false accepts. |
| D | success | Some executable-pass artifacts still need review escalation. |
| E | null | Cheap bounded repair does not beat equal-cost fresh generation here. |

## Secondary Formal Evidence

The paper also cites three bounded formal-evidence surfaces:

- [`runs/vericoding_formal_eval_v2/`](runs/vericoding_formal_eval_v2/)
- [`runs/vericoding_formal_eval_v2_2/`](runs/vericoding_formal_eval_v2_2/)
- [`runs/dafny_full_claude/`](runs/dafny_full_claude/)

See also the short interpretation note:
- [`runs/vericoding_research_v3/reports/verification_facade_dafny_note.md`](runs/vericoding_research_v3/reports/verification_facade_dafny_note.md)

These are **secondary evidence surfaces**, not the paper’s primary denominator.

## Path 1: Audit the Packaged Evidence  
**No API keys required**

This is the default reviewer path. It checks that the packaged artifact is internally consistent and that the paper-facing claims line up with the included ledgers, reports, and status files.

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

Expected headline claim labels in [`runs/vericoding_research_v3/reports/claim_status.json`](runs/vericoding_research_v3/reports/claim_status.json):
- `Claim A = success`
- `Claim B = partial`
- `Claim C = success`
- `Claim D = success`
- `Claim E = null`

## Path 2: Re-run the Live v3 Workflow  
**API keys required**

If you want to reproduce the live provider-backed workflow rather than just audit the packaged artifact, run it in a **fresh root** so you do not overwrite the packaged evidence.

This path requires an OpenAI API key in your shell environment. The wrapper script below sources `~/.zshrc` and exits early if `OPENAI_API_KEY` is unavailable.

```bash
git clone https://github.com/davidkimai/sps_evals.git
cd sps_evals
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
mkdir -p runs/reviewer_reruns
scripts/run_with_env.sh python3 scripts/run_vericoding_research_v3.py run-all --root runs/reviewer_reruns/vericoding_research_v3_rerun
scripts/run_with_env.sh python3 scripts/run_vericoding_research_v3.py status --root runs/reviewer_reruns/vericoding_research_v3_rerun
```

If the run is interrupted, resume it with:

```bash
scripts/run_with_env.sh python3 scripts/run_vericoding_research_v3.py resume --root runs/reviewer_reruns/vericoding_research_v3_rerun
```

Notes:
- The default live model is `gpt-5.4-mini`.
- This path is provider-backed and may incur cost.
- Because frontier APIs can drift, the right reproducibility standard is **claim-level and workflow-level reproducibility**, not byte-identical recreation of every original row.
- The packaged artifact in [`runs/vericoding_research_v3/`](runs/vericoding_research_v3/) remains the exact original evidence package cited by the paper.

## Short Agent Prompt

If you prefer an agent over manual terminal use, paste this:

```text
Open this repository as a reviewer. First audit the packaged evidence: read README.md, paper/paper.pdf, and runs/vericoding_research_v3/reports/reviewer_quickstart.md, then run the focused pytest suite, `python scripts/run_vericoding_research_v3.py audit-completion`, and `python scripts/run_vericoding_research_v3.py status`. Confirm whether the packaged v3 result reproduces, whether `conference_complete` and `final_submit_ready` are both true, and whether Claim A-E in runs/vericoding_research_v3/reports/claim_status.json match the paper. Then, if API keys are available, run the live workflow in a fresh root with `scripts/run_with_env.sh python3 scripts/run_vericoding_research_v3.py run-all --root runs/reviewer_reruns/vericoding_research_v3_rerun`, and report whether the regenerated run is directionally consistent with the packaged claims.
```

## Canonical Evidence

For the main study, treat these append-only ledgers as canonical truth:

- [`runs/vericoding_research_v3/ledgers/candidate_bank.jsonl`](runs/vericoding_research_v3/ledgers/candidate_bank.jsonl)
- [`runs/vericoding_research_v3/ledgers/selector_eval.jsonl`](runs/vericoding_research_v3/ledgers/selector_eval.jsonl)
- [`runs/vericoding_research_v3/ledgers/e2e_runs.jsonl`](runs/vericoding_research_v3/ledgers/e2e_runs.jsonl)
- [`runs/vericoding_research_v3/ledgers/secure_eval.jsonl`](runs/vericoding_research_v3/ledgers/secure_eval.jsonl)
- [`runs/vericoding_research_v3/ledgers/triage_decisions.jsonl`](runs/vericoding_research_v3/ledgers/triage_decisions.jsonl)
- [`runs/vericoding_research_v3/ledgers/manual_adjudication.jsonl`](runs/vericoding_research_v3/ledgers/manual_adjudication.jsonl)

Use reports for synthesis and interpretation. Use Inspect logs as runtime provenance, not as the primary analysis database.

## Public Repo Layout

- [`paper/`](paper/) — canonical manuscript source and PDF
- [`runs/vericoding_research_v3/`](runs/vericoding_research_v3/) — main claim-bearing evidence package
- [`runs/vericoding_formal_eval_v2/`](runs/vericoding_formal_eval_v2/) — bounded Lean 4 formal-evaluator slice
- [`runs/vericoding_formal_eval_v2_2/`](runs/vericoding_formal_eval_v2_2/) — targeted Lean 4 review-boundary follow-up
- [`runs/dafny_full_claude/`](runs/dafny_full_claude/) — historical Dafny evidence cited in the paper
- [`src/`](src/) — evaluation/runtime code
- [`data/`](data/) — frozen task/spec surfaces
- [`formal/`](formal/) — Lean 4 formal harness source
- [`scripts/`](scripts/) — top-level audit/run entrypoints
- [`tests/`](tests/) — focused audit-oriented test subset

## Provider-Backed Wrapper Scripts

If you want to run provider-backed commands directly, use the sourced-shell wrappers so API keys and toolchain variables come from your shell environment:

```bash
scripts/run_with_env.sh python3 scripts/run_vericoding_research_v3.py status
scripts/run_with_env_formal.sh python3 scripts/run_vericoding_formal_eval_v2_2.py status
```

## License

MIT
