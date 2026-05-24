# inspect_evals_register_example

- URL: https://raw.githubusercontent.com/UKGovernmentBEIS/inspect_evals/main/register/example_eval.yaml
- Retrieved: 2026-05-19T08:07:05Z
- Status: cached
- Failure reason: none
- Cache path: `runs/vericoding_research_v3/provenance/reading_cache/inspect_evals_register_example.txt`
- SHA256: `203d0513509385539f59479ec54085bc21f098d715390f40944551c3e2862e3f`

## Takeaways

- Grounding resource for Track 3 full-program execution.
- Used to lock the trust-boundary triage object, Inspect provenance stance, or SPS review-boundary framing.
- Exact claims remain derived from local ledgers, not from this source.

## Excerpt

# Example eval.yaml for a register entry. # # Copy this file to `register/ /eval.yaml` and fill in the # values. Lines marked "optional" can be deleted if not used. # # The authoritative schema lives in the pydantic models in # `src/inspect_evals/metadata.py`: # - ExternalEvalMetadata (top-level fields) # - ExternalEvalSource (the `source` block) # - EvalRuntimeMetadata (the `metadata` block) # - EvaluationReport (the `evaluation_report` block) # - EvaluationReportResult (each row in `evaluation_report.results`) # - EvaluationReportMetric (each entry in a row's `metrics`) # # `id` is auto-injected from the directory name (e.g. `register/my-eval/` # becomes id `my-eval`) and must NOT be set here. title: "My Eval" description: | What this eval measures. One short paragraph is plenty — the generated README links back to the upstream repo for full detail. arxiv: "https://arxiv.org/abs/2401.00000" # optional; URL to the paper contributors: - my-github-handle # whoever opened this PR tags: # optional; the upstream repo name is added automatically - Coding metadata: # optional; alias for `runtime_metadata`. Use the key `metadata` in YAML. fast: false # optional; default false or omitted. Set true if samples average # grab from the commit page on GitHub; tags and branches aren't accepted maintainers: # optional; defaults to [ ] parsed from repository_url - upstream-owner # set explicitly when the repo is org-owned and the real maintainers are individuals comment: "Optional note about this source." # evaluation_report is optional. If present, it renders as a results table # in the generated README. evaluation_report: timestamp: "July 2025" # optional commit: # required: the upstream commit the run was against (may differ from source.repository_commit if the pin has since been bu
