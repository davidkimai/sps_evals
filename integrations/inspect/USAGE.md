# Local Inspect Usage

Install the optional Inspect surface:

```bash
python3 -m pip install -e '.[inspect]'
```

Run a no-provider internal smoke:

```bash
inspect eval slopbench_internal_smoke \
  -T variant=reference \
  --limit 1 \
  --model mockllm/model \
  --no-log-samples --no-log-realtime --no-fail-on-error
```

Run the parity harness:

```bash
python3 scripts/inspect_parity_check.py --run-live
```

Inspect-native external subset tasks intentionally load only sanitized manifests
by default. Raw SCBench prompts/tests are quarantined and must not be committed
through Inspect logs. Paid external execution should use ignored runtime logs and
the repaired Sprint 8.5 defaults: all checkpoints, full-file output, and
`max_tokens=12000`.

The first paid ladder is:

1. two-problem `baseline` smoke,
2. two-problem `baseline + hybrid` smoke,
3. fixed subset `baseline + hybrid`,
4. add `karpathy` only after technical cleanliness or signal.
