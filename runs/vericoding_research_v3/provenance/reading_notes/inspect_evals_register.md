# inspect_evals_register

- URL: https://raw.githubusercontent.com/UKGovernmentBEIS/inspect_evals/main/EVAL_REGISTER.md
- Retrieved: 2026-05-19T08:07:05Z
- Status: cached
- Failure reason: none
- Cache path: `runs/vericoding_research_v3/provenance/reading_cache/inspect_evals_register.txt`
- SHA256: `3317124ddf33e79cdd75e0dff60d9035210dde6aafcc42e6d7d1d3faad93e930`

## Takeaways

- Grounding resource for Track 3 full-program execution.
- Used to lock the trust-boundary triage object, Inspect provenance stance, or SPS review-boundary framing.
- Exact claims remain derived from local ledgers, not from this source.

## Excerpt

# Eval Register Inspect Evals provides a way to share Inspect eval implementations with the broader community. However, as the number of evaluations grew, we found that maintaining quality and compatibility in a single package was not sustainable. As of the 8th of May 2026, Inspect Evals will stop accepting eval code submissions into `/src`. To register new evals, contributors can submit a simple .yaml file that points to an externally managed repo that hosts the eval. This move towards a distributed register model mirrors the approach taken by other projects that faced similar problems, such as Helm/charts, Terraform Registry, and Docker Official Images. > [!TIP] > This doc primarily serves as a background explainer for contributors who want to understand why we moved to a register model. > Seeking a guide to help register an evaluation whose code lives in a separate upstream repository? See the [Submission Guide](register/README.md). ## Table of Contents - [Background](#background) - [Introducing: The Inspect Evals Register](#introducing-the-inspect-evals-register) - [FAQ](#faq) ## Background ### Where Inspect Evals Started Inspect Evals was [launched in May 2024](https://www.aisi.gov.uk/blog/inspect-evals) as a collection of example evaluations for the Inspect AI framework. It was intended to foster community collaboration and make it easy to run, experiment and share Inspect AI evaluations. In the past, we've done this by accepting PRs which submit evals directly to src/, with the intention that they can be installed and run locally from the Inspect registry. What started as a project to show a handful of evaluation examples now hosts 120+ evaluation implementations and 200+ Inspect AI tasks; with the growth, we started having to make trade-offs between opposing req
