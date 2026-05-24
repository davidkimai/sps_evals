from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Literal

Provider = Literal["openai", "anthropic", "google", "mock"]
GenerationMode = Literal[
    "baseline",
    "oracle",
    "oracle_karpathy",
    "oracle_dafny",
    "neutral_style",
    "hybrid",
    "modular_discovery",
]
OracleSource = Literal["zen", "karpathy", "dafny"]


ZEN_OF_PYTHON_PRIMITIVES: tuple[str, ...] = (
    "Beautiful is better than ugly.",
    "Explicit is better than implicit.",
    "Simple is better than complex.",
    "Complex is better than complicated.",
    "Flat is better than nested.",
    "Sparse is better than dense.",
    "Readability counts.",
    "Special cases are not special enough to break the rules.",
    "Although practicality beats purity.",
    "Errors should never pass silently.",
    "Unless explicitly silenced.",
    "In the face of ambiguity, refuse the temptation to guess.",
    "There should be one obvious way to do it.",
    "Although that way may not be obvious at first unless you are Dutch.",
    "Now is better than never.",
    "Although never is often better than right now.",
    "If the implementation is hard to explain, it is a bad idea.",
    "If the implementation is easy to explain, it may be a good idea.",
    "Namespaces are one honking great idea -- let's do more of those!",
)

ZEN_ORACLE_SPEC = """\
Treat the Zen of Python as an informal in-context oracle for structural quality.
The oracle is not a style preference layer; it is a degree-of-freedom collapse
over the implementation space. Preserve functional correctness while choosing
the simplest architecture that satisfies the task.

Operational constraints:
- Prefer small pure helpers over monolithic functions.
- Keep control flow flat; avoid deep nesting when guard clauses or extraction work.
- Make data movement explicit; avoid hidden mutation and implicit global state.
- Raise clear errors for invalid inputs instead of silently guessing.
- Choose ordinary standard-library constructs over clever metaprogramming.
- Use names that make the implementation easy to explain.
- Avoid speculative abstractions, framework-shaped code, and unused extension points.
- Keep code sparse enough that a maintainer can audit behavior locally.
"""

KARPATHY_ORACLE_SPEC = """\
Treat the Karpathy Guidelines as an informal in-context oracle for structural
quality. The oracle is not a style preference layer; it is a degree-of-freedom
collapse over the implementation space. Preserve functional correctness while
choosing the simplest architecture that satisfies the task.

Operational constraints derived from Karpathy's behavioral guidelines
(https://github.com/forrestchang/andrej-karpathy-skills):
- Think before coding: state assumptions explicitly; if uncertain about a design
  choice, choose the most conservative interpretation.
- Simplicity first: write the minimum code that solves the problem. No features
  beyond what was asked. No abstractions for single-use code. No speculative
  flexibility or configurability. If you write 200 lines and it could be 50,
  rewrite it.
- Surgical changes: touch only what you must. Do not improve adjacent code,
  comments, or formatting. Match existing style even if you would do it
  differently.
- Goal-driven execution: define verifiable success criteria. Every function
  should have a clear, testable contract. Prefer writing tests first, then
  implementation.
"""

BASELINE_SYSTEM_PROMPT = """\
You are a secure program synthesis engineer. Generate a correct, reviewable Python
module for the task. Return only Python code. Do not include markdown prose.
"""

NEUTRAL_STYLE_SPEC = "Write clean, maintainable Python without a task-specific informal oracle."

NEUTRAL_STYLE_SYSTEM_PROMPT = """\
You are a secure program synthesis engineer. Generate a correct, clean,
maintainable Python module for the task. Return only Python code. Do not include
markdown prose.
"""

MODULAR_DISCOVERY_SYSTEM_PROMPT = """\
You are a secure program synthesis engineer. Generate a correct, reviewable
implementation artifact for the task. You have access to skill discovery before
solving. Load the most relevant skill with get_skill when a listed skill applies,
then use that skill as the active oracle for the final implementation. Return
Python source unless the loaded skill explicitly requires Dafny source. Do not
include markdown prose.
"""

ZEN_ORACLE_SYSTEM_PROMPT = f"""\
You are a secure program synthesis engineer. Generate a correct, reviewable Python
module for the task. Return only Python code. Do not include markdown prose.

{ZEN_ORACLE_SPEC}

Zen of Python primitives:
{chr(10).join(f"- {line}" for line in ZEN_OF_PYTHON_PRIMITIVES)}
"""

KARPATHY_ORACLE_SYSTEM_PROMPT = f"""\
You are a secure program synthesis engineer. Generate a correct, reviewable Python
module for the task. Return only Python code. Do not include markdown prose.

{KARPATHY_ORACLE_SPEC}
"""

DAFNY_ORACLE_SYSTEM_PROMPT = """\
You are a secure program synthesis engineer using Dafny as a hard verification
oracle. Generate a small Dafny program for the task. Return only Dafny source.
Do not include markdown prose.

The generated Dafny source is a model-authored formal artifact. Verification
establishes the properties stated in that artifact; it is not by itself proof
that the original natural-language task was fully specified. Keep requires,
ensures, invariants, ghost state, and lemmas minimal and auditable.
"""

CUSTOM_ORACLE_SYSTEM_TEMPLATE = """\
You are a secure program synthesis engineer. Generate a correct, reviewable Python
module for the task. Return only Python code. Do not include markdown prose.

Treat the following task-specific informal specification as the in-context oracle
for structural quality. It overrides the Zen of Python for this task. Preserve
functional correctness while collapsing implementation degrees of freedom around
this spec.

Task-specific informal oracle:
{oracle_spec}
"""

GENERATION_USER_TEMPLATE = """\
Task id: {task_id}
Entry point: {entry_point}

Functional requirements:
{prompt}

Synthesis instructions:
- Return a complete Python module.
- Keep imports standard-library only unless the task explicitly permits otherwise.
- Do not include tests in the generated module.
- Do not perform network, filesystem, or subprocess operations unless required.
"""

DAFNY_GENERATION_USER_TEMPLATE = """\
Task id: {task_id}
Entry point: {entry_point}

Functional requirements:
{prompt}

Dafny synthesis instructions:
- Return a complete Dafny source file only.
- Use standard Dafny methods/functions with explicit requires/ensures where useful.
- Keep proof structure minimal: no speculative lemmas, ghost state, or abstractions.
- The code will be verified with Dafny, translated to Python, and then measured/tested
  as the compiled Python artifact.
"""

MAINTENANCE_SYSTEM_PROMPT = """\
You are a secure program synthesis maintenance agent. Given an existing Python
module and a Day 2 feature requirement, return a complete replacement module
that preserves the original functional contract and implements the new behavior.
Return only Python code. Do not include markdown prose.
"""

MAINTENANCE_USER_TEMPLATE = """\
Task id: {task_id}
Entry point: {entry_point}

Original functional requirements:
{prompt}

Existing solution.py:
```python
{code}
```

Day 2 maintenance requirement:
{day2_prompt}

Maintenance instructions:
- Return a complete replacement Python module.
- Preserve all original behavior unless the Day 2 requirement explicitly changes it.
- Keep imports standard-library only unless the task explicitly permits otherwise.
- Prefer the smallest clear edit that keeps the module easy to audit.
"""

JUDGE_SYSTEM_PROMPT = """\
You are an expert secure program synthesis reviewer. Score how well the candidate
implementation follows the informal Zen of Python oracle while preserving the
task semantics. Focus on structural quality: simplicity, explicitness, flatness,
readability, local auditability, and absence of architectural slop.

Return strict JSON only. Do not include markdown.
"""

JUDGE_USER_TEMPLATE = """\
Task id: {task_id}
Entry point: {entry_point}

Functional requirements:
{prompt}

Informal structural spec to judge against:
{oracle_spec}

Candidate code:
```python
{code}
```

Return this JSON shape exactly:
{{
  "score": 1,
  "rationale": "one concise paragraph",
  "strengths": ["short bullet"],
  "weaknesses": ["short bullet"]
}}

The score must be an integer from 1 to 10, where 10 means the implementation is
an excellent in-context realization of the informal oracle and 1 means severe
architectural slop.
"""


@dataclass(frozen=True)
class ModelSettings:
    provider: Provider
    model: str
    temperature: float = 0.2
    max_tokens: int = 4096
    timeout_seconds: float = 60.0
    api_key_env: str = "OPENAI_API_KEY"
    require_temperature: bool = False


@dataclass(frozen=True)
class Task:
    id: str
    prompt: str
    test_code: str
    day2_prompt: str
    day2_test_code: str
    day2_stressors: tuple[str, ...]
    human_reference: str
    entry_point: str = "solution"
    tags: tuple[str, ...] = ()
    custom_spec_override: str | None = None
    mock_solution: str | None = None
    mock_day2_solution: str | None = None

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "Task":
        required = (
            "id",
            "prompt",
            "test_code",
            "day2_prompt",
            "day2_test_code",
            "day2_stressors",
            "human_reference",
        )
        missing = [key for key in required if not payload.get(key)]
        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"task is missing required field(s): {joined}")

        tags = payload.get("tags") or ()
        if isinstance(tags, str):
            tags = (tags,)
        day2_stressors = payload.get("day2_stressors") or ()
        if isinstance(day2_stressors, str):
            day2_stressors = (day2_stressors,)

        return cls(
            id=str(payload["id"]),
            prompt=str(payload["prompt"]),
            test_code=str(payload["test_code"]),
            day2_prompt=str(payload["day2_prompt"]),
            day2_test_code=str(payload["day2_test_code"]),
            day2_stressors=tuple(str(stressor) for stressor in day2_stressors),
            human_reference=str(payload["human_reference"]),
            entry_point=str(payload.get("entry_point") or "solution"),
            tags=tuple(str(tag) for tag in tags),
            custom_spec_override=(
                str(payload["custom_spec_override"])
                if payload.get("custom_spec_override") is not None
                else None
            ),
            mock_solution=(
                str(payload["mock_solution"]) if payload.get("mock_solution") is not None else None
            ),
            mock_day2_solution=(
                str(payload["mock_day2_solution"])
                if payload.get("mock_day2_solution") is not None
                else None
            ),
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "prompt": self.prompt,
            "test_code": self.test_code,
            "day2_prompt": self.day2_prompt,
            "day2_test_code": self.day2_test_code,
            "day2_stressors": list(self.day2_stressors),
            "human_reference": self.human_reference,
            "entry_point": self.entry_point,
            "tags": list(self.tags),
            "custom_spec_override": self.custom_spec_override,
            "mock_solution": self.mock_solution,
            "mock_day2_solution": self.mock_day2_solution,
        }


def default_model_settings(
    provider: Provider,
    *,
    role: Literal["generator", "judge", "maintenance"],
) -> ModelSettings:
    prefix = f"SPECORACLE_{role.upper()}"
    if provider == "anthropic":
        model = os.getenv(f"{prefix}_MODEL", "claude-sonnet-4-6")
        api_key_env = os.getenv(f"{prefix}_API_KEY_ENV", "ANTHROPIC_API_KEY")
    elif provider == "google":
        model = os.getenv(f"{prefix}_MODEL", "gemini-2.5-pro")
        api_key_env = os.getenv(f"{prefix}_API_KEY_ENV", "GEMINI_API_KEY")
    elif provider == "mock":
        model = os.getenv(f"{prefix}_MODEL", "mock-local")
        api_key_env = "SPECORACLE_NO_API_KEY"
    else:
        model = os.getenv(f"{prefix}_MODEL", "gpt-5.5")
        api_key_env = os.getenv(f"{prefix}_API_KEY_ENV", "OPENAI_API_KEY")

    return ModelSettings(
        provider=provider,
        model=model,
        temperature=float(os.getenv(f"{prefix}_TEMPERATURE", "0.2")),
        max_tokens=int(os.getenv(f"{prefix}_MAX_TOKENS", "4096")),
        timeout_seconds=float(os.getenv(f"{prefix}_TIMEOUT_SECONDS", "60")),
        api_key_env=api_key_env,
        require_temperature=False,
    )


def oracle_spec_for_task(task: Task, *, source: OracleSource = "zen") -> str:
    if task.custom_spec_override:
        return task.custom_spec_override.strip()
    if source == "dafny":
        return "Dafny formal verification skill loaded through modular discovery."
    if source == "karpathy":
        return KARPATHY_ORACLE_SPEC
    return ZEN_ORACLE_SPEC


def oracle_spec_label_for_task(task: Task, *, source: OracleSource = "zen") -> str:
    if task.custom_spec_override:
        return "custom_spec_override"
    if source == "dafny":
        return "dafny_formal_verification"
    if source == "karpathy":
        return "karpathy_oracle"
    return "zen_of_python"


def system_prompt_for_mode(mode: GenerationMode, *, task: Task | None = None) -> str:
    if mode == "baseline":
        return BASELINE_SYSTEM_PROMPT
    if mode == "modular_discovery":
        return MODULAR_DISCOVERY_SYSTEM_PROMPT
    if mode == "neutral_style":
        return NEUTRAL_STYLE_SYSTEM_PROMPT
    if mode == "oracle_karpathy":
        if task is not None and task.custom_spec_override:
            return CUSTOM_ORACLE_SYSTEM_TEMPLATE.format(oracle_spec=oracle_spec_for_task(task))
        return KARPATHY_ORACLE_SYSTEM_PROMPT
    if mode == "oracle_dafny":
        return DAFNY_ORACLE_SYSTEM_PROMPT
    if mode in {"oracle", "hybrid"}:
        if task is not None and task.custom_spec_override:
            return CUSTOM_ORACLE_SYSTEM_TEMPLATE.format(oracle_spec=oracle_spec_for_task(task))
        return ZEN_ORACLE_SYSTEM_PROMPT
    raise ValueError(f"unknown generation mode: {mode}")


def variant_name(mode: GenerationMode) -> str:
    if mode == "baseline":
        return "baseline_generation"
    if mode == "oracle":
        return "oracle_generation"
    if mode == "oracle_karpathy":
        return "oracle_karpathy_generation"
    if mode == "oracle_dafny":
        return "oracle_dafny_generation"
    if mode == "hybrid":
        return "hybrid_generation"
    if mode == "modular_discovery":
        return "modular_discovery_generation"
    if mode == "neutral_style":
        return "neutral_style_generation"
    raise ValueError(f"unknown generation mode: {mode}")
