# Verification-Facade Dafny Note

The Dafny history is retained as a verification-facade warning, not as a main result.

## Audited Signal

The historical `runs/dafny_full_claude/` surface contains 150 oracle Dafny rows. Fifty-two rows have `verified=true`; all verified rows have judge score 1, and none has judge score greater than 3.

The common failure mode is operational mismatch:

- the Dafny artifact verifies a local property but fails the Python task boundary;
- compiled wrappers obscure or break the expected interface;
- proof status does not guarantee that the deployed artifact is the thing the system needs;
- local verification can coexist with runtime failure or semantic noncompliance.

## Trust-Boundary Lesson

This supports the v3 review-boundary framing. A stronger evaluator layer cannot stop at proof status. It must ask whether the accepted artifact satisfies the operational interface, executable tests, security checks, and review assumptions.

## Submission Use

Use Dafny only as:

- appendix context;
- a bounded discussion of verification-facade risk;
- support for Claim D's review-boundary necessity.

Do not use Dafny to reopen the main evidence program.
