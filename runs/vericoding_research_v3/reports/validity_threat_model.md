# Validity Threat Model

Created: 2026-05-19T06:57:18Z

| Threat | Mitigation |
|---|---|
| Prompt/evaluator contamination | visible secure spec source and forbidden-source test |
| Synthetic evidence counted as final | completion excludes proxy/canary/fallback rows |
| Selector leakage | anonymized observable view |
| Confirmatory tuning | policy and manifest freeze before confirmatory |
| Repair overclaim | equal-cost repair baseline |
| Stochastic overclaim | logged replicate semantics |
