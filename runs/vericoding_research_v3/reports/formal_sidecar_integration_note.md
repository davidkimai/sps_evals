# Formal Sidecar Integration Note

## Executive judgment

The new formal results should be integrated as **bounded convergent evidence** for the main trust-boundary paper object, not as a new project center.

The scientifically strongest framing is:

- the **main paper object** remains the 24-task executable trust-boundary gate,
- the **historical Dafny evidence** remains a warning about verification-façade and wrapper/interface failure,
- the **new bounded Lean 4 formal-evaluator experiments** show that narrow formal evaluators can help in exactly the way the paper claims: by hardening acceptance decisions and, crucially, by preserving explicit review boundaries rather than dissolving them.

## The most compelling attractors

### 1. Formal evidence can harden a gate without becoming the whole gate

`runs/vericoding_formal_eval_v2/` is most valuable as a bounded proof that the trust-boundary story survives contact with a mechanized formal slice.

What to say:
- on a 6-task Lean-backed slice,
- visible-pass / formal-fail behavior still appears,
- support-conditioned ranking still matters,
- and once support is present, the formal selector reduces bounded-slice false accepts from `3` to `0`.

This is not a theorem-prover-native SPS victory lap. It is evidence that the main paper's acceptance-layer thesis is robust even when one evaluator layer becomes more formal.

### 2. The most important formal result is not "proof says yes" but "formal pass still does not settle deployment"

`runs/vericoding_formal_eval_v2_2/` adds the missing review-boundary result.

The strongest flagship case is:
- `timing_safe_compare:gpt-5.4-mini:behavioral_minimal_prompt:formal:0`
- `visible_tests_pass = true`
- `formal_pass = true`
- final decision = `escalate_to_review`

Reason:
- the bounded formal I/O contract does not certify constant-time behavior,
- so a candidate that passes the mechanized slice still does **not** automatically earn deployment authorization.

This is the cleanest formal-methods-adjacent demonstration of the paper's triage worldview:
- some artifacts should be accepted,
- some should be rejected,
- and some should be explicitly paused for human review even after strong automated evidence.

### 3. The right contrast is "bounded formal help" versus "formal theater", not "formal methods failed"

The historical Dafny result and the new Lean result are strongest when presented together:

- **Dafny history:** strong-looking proof-bearing status repeatedly failed the operational Python boundary.
- **Lean 4 formal evaluator:** a narrow formal evaluator can still provide real value on tiny trust-boundary components.
- **Shared lesson:** even good formal evidence only means what its wrapper, interface, and TCB assumptions allow it to mean.

This yields a much better SPS/security story than either extreme:
- not "formal methods solve the problem now," and
- not "formal methods are useless."

Instead:
- formal methods help most when they are used narrowly, honestly, and inside a larger trust-boundary workflow.

## How to talk about this in the SPS / security community

### Lead with the main paper, not the sidecar

The order should be:
1. visible-pass / hidden-fail,
2. secure rejection,
3. support-conditioned ranking,
4. review-boundary triage,
5. then: "we also tested a bounded Lean 4 formal evaluator, and it reinforced the same trust-boundary story rather than replacing it."

### Use the sidecar to strengthen credibility, not novelty inflation

The sidecar helps because it shows:
- we did not stop at a generic hidden-test story,
- we checked whether a more formal evaluator layer changes the operational picture,
- and the answer was: it helps, but it still terminates in review boundaries.

That is reviewer-robust and intellectually honest.

### The best one-sentence pitch

> A bounded Lean 4 formal evaluator reinforced the main trust-boundary result: narrow formal evaluators can harden acceptance decisions on tiny security-critical components, but even formal-pass artifacts can still require explicit human review before deployment.

## What to integrate into paper text

Use the sidecar in **Discussion**, not as a new headline contribution.

Best compact paper move:
- keep the existing Dafny/review-boundary paragraph,
- add one short paragraph after it saying that a newer bounded Lean 4 formal evaluator gave a more positive but still bounded result,
- specifically mention that a targeted follow-up produced a confirmatory `formal_pass / review_required` timing-safe case,
- interpret this as support for the acceptance-layer thesis rather than a new formal-synthesis claim.

## What not to do

- Do not replace the main denominator with the formal slice.
- Do not add a new top-level paper act centered on Lean.
- Do not treat the sidecar as end-to-end formal synthesis.
- Do not present the Dafny history as an anti-formal-methods result.
- Do not let the formal story obscure the stronger main attractors: visible-pass / hidden-fail, secure rejection, and triage.

## Canonical supporting paths

Main bounded formal slice:
- `runs/vericoding_formal_eval_v2/reports/final_synthesis.md`
- `runs/vericoding_formal_eval_v2/reports/claim_status.json`

Targeted review-boundary slice:
- `runs/vericoding_formal_eval_v2_2/reports/final_synthesis.md`
- `runs/vericoding_formal_eval_v2_2/reports/formal_review_boundary_casebook.md`
- `runs/vericoding_formal_eval_v2_2/reports/senior_judgment.md`

Historical cautionary baseline:
- `runs/vericoding_research_v3/reports/verification_facade_dafny_note.md`
