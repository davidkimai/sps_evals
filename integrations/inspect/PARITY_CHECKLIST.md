# Sprint 9 Inspect Parity Checklist

## Hard Parity

- [ ] Same-artifact pytest pass/fail is exact.
- [ ] Same-artifact structural metrics match within `1e-6`.
- [ ] Canned hybrid gate behavior is exact.
- [ ] Canned retry counts are exact.
- [ ] Sanitized failure categories match on fixture failures.

## Soft Parity

- [ ] Token estimates are directionally comparable, not exact.
- [ ] Live model outputs are interpreted as directional, not row-exact.
- [ ] External trajectory summaries are compared by problem/checkpoint joins,
      not row order.

## External Preconditions

- [ ] Pinned SCBench revision and fingerprint recorded.
- [ ] Local subset manifest SHA recorded.
- [ ] Tracked artifacts contain only hashes, metadata, generated code, and
      sanitized outcomes.
- [ ] Raw prompts, tests, assertions, stdout, and stderr are not tracked.
