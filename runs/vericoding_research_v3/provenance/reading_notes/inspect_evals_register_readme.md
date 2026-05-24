# inspect_evals_register_readme

- URL: https://raw.githubusercontent.com/UKGovernmentBEIS/inspect_evals/main/register/README.md
- Retrieved: 2026-05-19T08:07:05Z
- Status: cached
- Failure reason: none
- Cache path: `runs/vericoding_research_v3/provenance/reading_cache/inspect_evals_register_readme.txt`
- SHA256: `eff5cf64569e554c72f1d5402662b8ba02228c7419aa2320378aa1c4951d5199`

## Takeaways

- Grounding resource for Track 3 full-program execution.
- Used to lock the trust-boundary triage object, Inspect provenance stance, or SPS review-boundary framing.
- Exact claims remain derived from local ledgers, not from this source.

## Excerpt

# Inspect Evals Register (Beta) User Guide The Inspect Evals Register aims to make it easier to submit, discover, and run evals that live in their authors' own repositories. It lists each eval in the [inspect_evals docs](https://ukgovernmentbeis.github.io/inspect_evals/) with a pointer to a pinned commit of the upstream repo. This guide outlines how to register (and update) evaluations in the Inspect Evals docs. For background on why the project moved to a register model, see [About the Register](https://github.com/UKGovernmentBEIS/inspect_evals/blob/main/EVAL_REGISTER.md). ## Contents - [How to run externally-managed evals](#how-to-run-externally-managed-evals) - [How to add an evaluation to the register](#how-to-add-an-evaluation-to-the-register) - [Upstream repo requirements](#upstream-repo-requirements) - [Steps to make the new-submission PR](#steps-to-make-the-new-submission-pr) - [How to update an evaluation in the register](#how-to-update-an-evaluation-in-the-register) - [Checks included in our automated submission workflow](#automated-register-submission-checks) - [Other contributions](#other-contributions) ## How to run externally-managed evals Users run registered evals by cloning the upstream repository at the pinned commit, installing its dependencies, and running `inspect eval` against the task file. Our doc auto-generation creates a `usage` section that walks through these steps for each registered eval. See below as an example: ![Usage section in the Inspect Evals docs, showing the clone, install, and `inspect eval` commands a user runs to execute a registered eval.](../docs/images/example-usage-section.png) ## How to add an evaluation to the register We designed the submission process to be lightweight. However, to plug into Inspect Evals' docs and workf
