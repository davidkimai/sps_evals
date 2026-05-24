# Paper Rewrite Doctrine

This doctrine controls the Track 3-facing paper rewrite.

## Title Direction

Use a title close to:

`Executable Trust-Boundary Triage for Autonomous Coding Agents`

The title should foreground verification and acceptance, not slop reduction.

## Abstract

Lead with:

- the bottleneck is accepting AI-written software, not merely generating it;
- visible tests are insufficient;
- hidden executable evaluators act as trust-boundary oracles;
- secure rejection is a positive result;
- ranking is support-conditioned;
- the system outputs accept, reject, or escalate.

## Introduction

The introduction should start from the Track 3 problem: how to verify what AI is writing. The primary motivation is a verification layer for autonomous code acceptance.

Avoid opening with cyclomatic complexity or informal structural taste. Those belong in prior-work lineage, not the main paper.

## Methods

Center the method around:

- owned 24-task narrow-waist denominator;
- visible vs hidden evaluator separation;
- provider-backed multi-candidate banks;
- fixed-bank selector comparison;
- triage policy over selected final artifacts;
- append-only ledgers as canonical evidence;
- Inspect logs as runtime provenance.

## Results

Use this order:

1. visible-pass / hidden-fail under the primary core;
2. secure rejection and false-accept reduction;
3. support-conditioned ranking and support generation bottleneck;
4. accept/reject/escalate triage;
5. bounded repair null;
6. external, SCBench, v2, and formal surfaces as context or demotions.

## Discussion

The discussion should emphasize:

- executable evaluator strength;
- no-ship decisions;
- support generation as the mechanism bottleneck;
- review surfaces after executable checks pass;
- why proof status or external rows are not allowed to overclaim.

## Limitations

State plainly:

- bounded denominator;
- support-starved internal tasks;
- Claim B remains partial;
- repair is null;
- external and SCBench surfaces are demoted;
- formal/Dafny evidence is bounded and secondary.
