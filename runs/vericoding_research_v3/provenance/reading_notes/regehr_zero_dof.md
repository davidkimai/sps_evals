# regehr_zero_dof

- URL: https://john.regehr.org/writing/zero_dof_programming.html
- Retrieved: 2026-05-19T08:07:05Z
- Status: cached
- Failure reason: none
- Cache path: `runs/vericoding_research_v3/provenance/reading_cache/regehr_zero_dof.txt`
- SHA256: `780f88ce93578812a3375fe0f4654f6b7b059dd1f8d4f635b45713c7921c9516`

## Takeaways

- Grounding resource for Track 3 full-program execution.
- Used to lock the trust-boundary triage object, Inspect provenance stance, or SPS review-boundary framing.
- Exact claims remain derived from local ledgers, not from this source.

## Excerpt

zero_dof_programming /* Default styles provided by pandoc. ** See https://pandoc.org/MANUAL.html#variables-for-html for config info. */ span.smallcaps{font-variant: small-caps;} div.columns{display: flex; gap: min(4vw, 1.5em);} div.column{flex: auto; overflow-x: auto;} div.hanging-indent{margin-left: 1.5em; text-indent: -1.5em;} /* The extra [class] is a hack that increases specificity enough to override a similar rule in reveal.js */ ul.task-list[class]{list-style: none;} ul.task-list li input[type="checkbox"] { font-size: inherit; width: 0.8em; margin: 0 0.8em 0.2em -1.6em; vertical-align: middle; } .display.math{display: block; text-align: center; margin: 0.5rem auto;} Zero-Degree-of-Freedom LLM Coding using Executable Oracles John Regehr , March 26 2026. You Can’t Trust The Damn Things By this point, most of us who have experimented with Claude, Codex, and other LLM-based coding agents have noticed that the current generation of these can sometimes do good work, at superhuman speed, when given some kinds of highly constrained tasks. For example, coding agents can eat a large, tricky API—such as the one for manipulating LLVM IR—for lunch, and they’ve also given me a number of fixes to non-trivial bugs in real software that could be applied as-is. On the other hand, these same tools frequently fall over in baffling ways, emitting tasteless or nonsensical code. When an LLM has the option of doing something poorly, we simply can’t trust it to make the right choices. The solution, then, is clear: we need to take away the freedom to do the job badly. The software tools that can help us accomplish this are executable oracles . The simplest executable oracle is a test case—but test cases, even when there are a lot of them, are weak. Consider Claude’s C Compiler, which I wro
