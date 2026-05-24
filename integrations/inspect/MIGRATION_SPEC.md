# Sprint 9 Inspect Migration Spec

Sprint 9 adds a narrow Inspect-native execution path without replacing the
legacy `specoracle` CLI. The migration target is semantic preservation and
external-validation recovery, not full framework conversion.

## Frozen Semantics

- `baseline`: current secure-program-synthesis system prompt, Python-only output.
- `hybrid`: baseline generation plus structural gate/retry feedback. Native
  Inspect is preferred; a wrapper around legacy generation is acceptable if
  native retry semantics drift.
- `karpathy`: Karpathy structural oracle prompt, Python-only output.
- External SCBench runs use the repaired Sprint 8.5 regime: full checkpoint
  chain, full-file output, and `max_tokens=12000` unless a later logged
  decision changes it.

## Parity Layers

- Layer A deterministic artifact parity: same code artifact, exact pass/fail,
  and CC/nesting/MI/redundancy deltas within `1e-6`.
- Layer B canned solver parity: exact gate behavior, retry counts, and solver
  routing on synthetic outputs.
- Layer C tiny live parity: directional only; model nondeterminism is not a
  migration failure by itself.

## Claim Boundaries

Use `Inspect-native approximation`, `parity-checked`, `partial_signal`, and
`credible_floor`. Do not claim that Inspect migration proves transfer,
maintainability, security, or threshold science.

## Fallback Ladder

1. Native Inspect task, solver, scorer, and sandbox path.
2. Inspect task using thin wrappers around existing SpecOracle generation.
3. Inspect task wrapping the existing runner/evaluator semantics while keeping
   Inspect datasets, logs, and scorers as the shared substrate.
