# Terminal-Bench Sprint 10 Bridge

Sprint 10 treats Terminal-Bench 2.0 as a candidate comparison surface, not as an
assumed validation benchmark. SCBench remains the anchor benchmark for iterative
specification-refinement pressure; Terminal-Bench is currently only a
structurally scorable Python-slice candidate.

## Execution Posture

- Use Harbor natively through `uvx --from harbor==0.7.0 harbor`.
- Use `scripts/run_sprint10_closeout.py` as the canonical Sprint 10 closeout
  entrypoint. It creates `runs/sprint10_closeout_v1/`, freezes dev and
  confirmatory manifests, appends every trial to `data/raw/runs.jsonl`, and
  derives summaries/reports from that ledger.
- Treat Inspect as the task identity and reusable evaluation surface; Harbor is
  only the raw terminal execution backend.
- Keep raw Terminal-Bench task text, tests, terminal logs, and verifier output in
  ignored scratch or raw run directories.
- Track only sanitized task IDs, metadata hashes, artifact-family labels,
  structural/proxy metric summaries, cost summaries, and outcome labels.
- Do not launch paid comparison runs unless the versioned closeout package has
  frozen manifests and the closeout driver preflight passes.

## Interventions

- `baseline`: Harbor-native `codex` agent without structural artifact gating.
- `artifact_gated_terminal_agent`: dedicated command path in
  `scripts/run_terminalbench_artifact_gated.py`; it selects valid baseline rows,
  applies a structural gate, and builds one bounded repair-pass Harbor run with
  an explicit artifact-gated prompt template.
- `hybrid`: reserved for a future condition only if the Terminal-Bench
  implementation preserves the SCBench Hybrid semantics closely enough.
- `karpathy`: compactness-oriented code/script condition only if selected tasks
  produce meaningful code or script artifacts.

The current Sprint 10 bridge intentionally keeps `hybrid` and `karpathy` out of
Terminal-Bench until their semantics transport cleanly. The immediate ladder is:
complete baseline validity first, then use `artifact_gated_terminal_agent` on
the same slice; do not call that condition Hybrid.

## Versioned Closeout Driver

Initialize or inspect the versioned package without paid execution:

```bash
python3 scripts/run_sprint10_closeout.py status
```

Run the deterministic closeout when paid execution is intentionally authorized:

```bash
python3 scripts/run_sprint10_closeout.py run-all --allow-paid
```

The canonical evidence root is `runs/sprint10_closeout_v1/`. The append-only
ledger is `runs/sprint10_closeout_v1/data/raw/runs.jsonl`; summaries,
taxonomies, metrics, and the final synthesis are derived from that ledger.

Stable sample identity intentionally excludes condition:

```text
terminalbench:{slice}:{task_id}
```

Condition and scaffold identity are tracked separately in ledger fields such as
`condition`, `scientific_condition_name`, and `scaffold_or_condition_version`.

The closeout uses a METR-style role split:

- `dev`: the four thesis-relevant elicitation tasks.
- `confirmatory`: a frozen disjoint 6-8 task Python slice when the local audit
  pool supports it; otherwise the manifest records a downgraded size rather than
  reusing dev tasks.

## Commands

Download a raw task inventory into scratch space:

```bash
rm -rf /tmp/sps_terminal_bench_2_audit
mkdir -p /tmp/sps_terminal_bench_2_audit
uvx --from harbor==0.7.0 harbor dataset download terminal-bench@2.0 \
  -o /tmp/sps_terminal_bench_2_audit \
  --export
```

Build the sanitized Sprint 10A manifest and audit docs:

```bash
python3 scripts/run_terminalbench_subset.py audit \
  --audit-dir /tmp/sps_terminal_bench_2_audit \
  --manifest runs/sprint10_terminalbench_subset_manifest.json
```

Validate without paid execution:

```bash
python3 scripts/run_terminalbench_subset.py validate \
  --manifest runs/sprint10_terminalbench_subset_manifest.json
python3 scripts/run_terminalbench_subset.py dry-run \
  --manifest runs/sprint10_terminalbench_subset_manifest.json \
  --phase artifact_capture_smoke
python3 scripts/run_terminalbench_subset.py dry-run \
  --manifest runs/sprint10_terminalbench_subset_manifest.json \
  --phase baseline_slice
```

Collect sanitized Harbor result rows from an ignored raw job directory:

```bash
python3 scripts/collect_terminalbench_artifacts.py \
  --job-dir runs/sprint10_terminalbench_smoke/raw_jobs/<job-name> \
  --out-dir runs/sprint10_terminalbench_smoke \
  --variant baseline \
  --phase artifact_capture_smoke
```

Build the artifact-gated selection without launching a paid run:

```bash
python3 scripts/run_terminalbench_artifact_gated.py select \
  --baseline-summary runs/sprint10_terminalbench_primary/summary.csv \
  --manifest runs/sprint10_terminalbench_subset_manifest.json \
  --run-dir runs/sprint10_terminalbench_artifact_gated \
  --force-all
python3 scripts/run_terminalbench_artifact_gated.py dry-run \
  --baseline-summary runs/sprint10_terminalbench_primary/summary.csv \
  --manifest runs/sprint10_terminalbench_subset_manifest.json \
  --run-dir runs/sprint10_terminalbench_artifact_gated \
  --force-all
```

Paid execution is limited to the narrow live ladder. Broad 6-8 task comparison
remains blocked until the 4-task baseline slice is valid and complete, and the
artifact-gated condition has been run on the same completed slice.

## Sprint 10A.2 Live Ladder Status

- Run A, `artifact_capture_smoke`, completed on `modernize-scientific-stack`
  with `baseline` / `gpt-5.4-mini`; sanitized artifact capture succeeded.
- Run B, `baseline_slice`, started on the 4-task thesis-relevant Python slice.
  The repaired collector now counts only one row as a valid functional row; the
  other tracked row is diagnostic because the agent/verifier result was absent.
- The observed Run B rows are now labeled
  `terminalbench_python_slice_partial_live_attractor`, not a completed
  behavioral contrast.
- `artifact_gated_terminal_agent` has a dry-run/select command path, but no paid
  artifact-gated run should launch until the baseline slice is valid and
  complete. Do not call this condition `hybrid`.
