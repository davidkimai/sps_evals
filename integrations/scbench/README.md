# SlopCodeBench Bridge

This bridge supports Sprint 7 long-horizon structural-resilience experiments
without committing raw external benchmark content.

## Data Policy

- Raw SlopCodeBench prompts, tests, and checkpoints are read at run time from a
  local JSONL cache or from Hugging Face via `specoracle[scbench]`.
- Public outputs store row ids, hashes, selected/excluded counts, generated
  code, and aggregate metrics.
- Do not commit the raw cache. Use `artifacts/scbench_cache/` or another ignored
  local path for downloaded records.

## Example

```bash
python3 scripts/run_scbench_longitudinal.py \
  --dataset gabeorlanski/slopcodebench --config python --split test \
  --out runs/sprint7_scbench_claude_pilot \
  --selection-manifest-out runs/sprint7_scbench_selection_manifest.json \
  --audit-only --limit 12
```

After the full audit has been written, run the selected supported rows:

```bash
python3 scripts/run_scbench_longitudinal.py \
  --dataset gabeorlanski/slopcodebench --config python --split test \
  --out runs/sprint7_scbench_claude_pilot \
  --provider anthropic --model claude-sonnet-4-6 \
  --variants baseline zen karpathy hybrid modular \
  --samples 1 --limit 12 --resume
```

To fetch directly from Hugging Face instead of a JSONL file, install the
optional dependency:

```bash
python3 -m pip install '.[scbench]'
```

Pin `--revision <fixed_revision>` when the final external run is launched.
The runner first audits the full fetched split, then applies `--limit` and
other selection filters so benchmark population accounting is not contaminated
by pilot selection.
