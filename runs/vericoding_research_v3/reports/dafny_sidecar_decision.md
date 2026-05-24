# Dafny Sidecar Decision

## Decision

No new broad Dafny buildout should be launched for the Track 3 submission.

The formal material remains bounded and secondary:

- v3 formal overlay rows are retained as review-boundary evidence.
- historical Dafny rows are used only as verification-facade context.
- no Dafny generation campaign should be treated as a primary claim surface.

## Reasoning

The existing Dafny history is not evidence that a broad proof-first path is ready. The audited `runs/dafny_full_claude/` surface contains 150 oracle Dafny rows. Fifty-two rows have `verified=true`, but all verified rows have judge score 1, and none has judge score greater than 3. The dominant lesson is not formal success; it is that a proof-bearing artifact can still fail the operational Python interface, wrapper boundary, or task semantics.

That is scientifically useful, but only as a trust-boundary warning.

## Allowed Use

Dafny may be discussed in one bounded way:

- as a verification-facade case study showing that "verified" does not imply autonomous acceptance; or
- as a future proof-sidecar for 1-2 narrow-waist security tasks if it directly sharpens a review-boundary claim.

## Disallowed Use

Do not:

- reopen the denominator around Dafny;
- frame the paper as broad formal synthesis;
- revive compiled-to-Python Dafny generation as a main result;
- replace the v3 trust-boundary triage object with proof status.

## Submission Implication

The final paper should say that formal overlays are useful but not sufficient. The acceptance boundary remains operational: visible checks, hidden executable checks, secure/regression checks, and human review surfaces all matter.
