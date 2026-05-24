# Reviewer Defense FAQ

This note is not part of the main paper. It exists to make the strongest foreseeable reviewer objections easy to answer consistently.

## 1. Is this just another Python evaluation study?

No. The object under study is not generic code quality. It is a trust-boundary deployment gate for narrow-waist, security-relevant components. The main result is not a benchmark score; it is the reduction of secure false accepts when specifications act as executable evaluators.

## 2. Why should security people care?

Because the code under study sits on small trust boundaries and defensive primitives: authorization logic, parser boundaries, rate limiting, canonicalization, schema enforcement, tenant scoping, and related choke-point behavior. The main deployment question is whether visibly plausible code should be authorized past a release gate. The main positive result is that tests-only selection falsely authorizes insecure artifacts that specification-aware triage blocks.

## 3. Why is the narrow-waist denominator a strength rather than a weakness?

Because the paper is not trying to solve coherent specification for arbitrary monoliths. It is trying to study bounded trust-boundary decisions where executable evidence is still inspectable. The denominator is deliberately chosen to avoid the ``Specifications Don't Exist'' trap and to keep the evidence surface operationally meaningful.

## 4. What is actually novel here?

Not a new theorem-prover formalism. Not a new abstract theory of SPS. The contribution is a sharp empirical operationalization of a problem the literature has identified but not bottomed out empirically: what happens when you build the trust-boundary triage layer and run real candidate pools through it.

The best short answer is:

- secure false-accept reduction,
- ternary triage (`auto_accept`, `auto_reject`, `escalate_to_review`),
- fixed-pool evaluation that isolates selection from generation,
- and explicit review-boundary measurement.

## 5. Aren't the hidden executable checks just arbitrary secret tests?

That is the main methodological question and it should be answered directly, not waved away. See `oracle_construction_and_validation.md`.

Short answer:

- internal tasks use frozen day-2 harnesses attached to owned narrow-waist tasks,
- secure tasks use deterministic hidden oracles generated from frozen secure-task templates,
- visible and hidden surfaces are intentionally separated,
- and claim-bearing failures are backed by manual adjudication rather than accepted blindly.

## 6. Why does `escalate_to_review` count as a result rather than an escape hatch?

Because the deployment problem is genuinely ternary in practice. Some artifacts pass executable checks but still carry unresolved wrapper, interface, runtime, or TCB assumptions. Treating those cases as binary pass/fail would hide the exact review-boundary problem the paper is trying to expose. The metric is backed by nonzero observed cases rather than being a purely theoretical placeholder.

## 7. Doesn't the project just show that better evaluation can't replace better generation?

Yes — and that is one of the paper's useful negative results. The support-bottleneck finding matters because it blocks a naive interpretation that stronger evaluators can manufacture correctness. The paper argues for stronger deployment gates, not evaluator magic.

## 8. Why not make this a theorem-prover-native formal synthesis paper?

Because that is not where the evidence is strongest. The project is intentionally scoped to bounded, security-relevant deployment decisions that can be studied today. Formal-methods-adjacent evidence appears in the review-boundary framing and the Dafny wrapper-boundary note, but the main contribution is an executable deployment-gate workflow, not an end-to-end proof-producing synthesis system.

## 9. What is the right one-sentence description of the paper?

An SPS paper about trust-boundary deployment decisions for AI-generated security-relevant code, where specifications act as executable rejection oracles that suppress secure false accepts and expose review boundaries.
