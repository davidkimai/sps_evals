# Attractor Priority Order

This file records the priority order for final submission writing and any future polishing. The order is based on the packaged v3 evidence, not on older project history.

## 1. Visible-Pass / Hidden-Fail

Frame: visible tests systematically overstate autonomous acceptance confidence.

Why it leads: Claim A is already success-labeled and directly motivates hidden executable evaluators. The packaged claim registry records 16 confirmatory visible-pass / hidden-fail tasks and 8 secure visible-pass / hidden-secure-fail tasks.

## 2. Secure Rejection / False-Accept Reduction

Frame: specifications are useful not only for finding winners, but for blocking dangerous no-ship cases.

Why it is coequal: Claim C is the cleanest positive security result. Tests-only selectors falsely accept secure failures on 7 tasks; spec-aware selection reduces secure false accepts on 6 of them, leaving 1 specoracle secure false-accept task in the registry.

## 3. Support-Conditioned Ranking

Frame: ranking helps only when the bank contains hidden-correct support.

Why it matters: Claim B is partial, but intellectually valuable. It shows that selection is not magic: support generation is the bottleneck, especially on hard internal narrow-waist tasks.

## 4. Trust-Boundary Triage

Frame: the mature output is not pass/fail, but `auto_accept`, `auto_reject`, or `escalate_to_review`.

Why it differentiates the package: The project behaves like acceptance infrastructure rather than a benchmark leaderboard. The packaged evidence includes 72 triage decisions and 6 escalation cases.

## 5. Narrow-Waist Security-Critical Scope

Frame: secure synthesis becomes tractable first on coherent, reviewable, security-relevant components.

Why it protects the claims: The denominator is intentionally bounded. The project does not claim universal program synthesis or broad deployment safety.

## 6. Verification-Facade Resistance

Frame: proof or verification status can still miss the operational acceptance boundary.

Why it is secondary but useful: The Dafny history is most valuable as a warning about wrong-language, wrong-interface, and wrapper-boundary failures. It should sharpen the review-boundary story, not become the center.
