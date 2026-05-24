# SlopBench Inspect Integration Stub

This directory contains a pre-submission export stub adapting SpecOracle's empirical results to the UK AISI's Inspect ecosystem.

> [!IMPORTANT]
> This stub demonstrates structural alignment with the `inspect_evals` schema. The full integration—including porting SpecOracle's Dockerized sandbox and CEGIS-style Hybrid Oracles into native Inspect Solvers—is the primary focus of the 4-month fellowship period.

## References

- Inspect Ecosystem: https://inspect.aisi.org.uk/
- UK AISI Inspect Evals: https://github.com/UKGovernmentBEIS/inspect_evals

## Exporting Sprint Evidence

```bash
python3 integrations/inspect/export.py \
  runs/slopbench_min_hybrid_claude \
  --out integrations/inspect/inspect_results.json
```

The exporter translates a SpecOracle `summary.csv` into a compact JSON payload containing dataset metadata, model identifiers, and variant-level architectural metrics ready for ingestion into the broader alignment evaluation network.
