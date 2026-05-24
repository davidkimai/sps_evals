from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from radon.complexity import cc_visit

from specoracle.config import GENERATION_USER_TEMPLATE, ModelSettings, Task, system_prompt_for_mode
from specoracle.evaluator import PytestResult, StaticMetrics, compute_static_metrics, run_pytest_for_code
from specoracle.generator import (
    GenerationResult,
    LLMClient,
    extract_python_code,
    token_estimate_summary,
)


@dataclass(frozen=True)
class HybridConstraints:
    max_cc: int | None = None
    max_nesting: int | None = None
    require_pytest: bool = True
    max_retries: int = 3


@dataclass(frozen=True)
class HybridAttempt:
    attempt_index: int
    code: str
    raw_response: str
    static_metrics: StaticMetrics
    pytest: PytestResult
    gate_failures: dict[str, Any]
    feedback_prompt: str | None = None

    def to_json_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["static_metrics"] = asdict(self.static_metrics)
        payload["pytest"] = asdict(self.pytest)
        return payload


class HybridOracle:
    """CEGIS-inspired soft oracle plus hard executable gate loop."""

    def __init__(
        self,
        *,
        client: LLMClient,
        settings: ModelSettings,
        constraints: HybridConstraints,
        pytest_timeout_seconds: float = 10.0,
    ) -> None:
        self._client = client
        self._settings = settings
        self._constraints = constraints
        self._pytest_timeout_seconds = pytest_timeout_seconds

    def generate_with_gates(
        self,
        *,
        task: Task,
        sample_index: int = 0,
    ) -> GenerationResult:
        system_prompt = system_prompt_for_mode("hybrid", task=task)
        user_prompt = GENERATION_USER_TEMPLATE.format(
            task_id=task.id,
            entry_point=task.entry_point,
            prompt=task.prompt.strip(),
        )
        active_prompt = user_prompt
        attempts: list[HybridAttempt] = []
        feedback_prompts: list[str] = []
        token_turns: list[tuple[str, str]] = []

        for attempt_index in range(self._constraints.max_retries + 1):
            if self._settings.provider == "mock" and task.mock_solution:
                raw_response = task.mock_solution
            else:
                raw_response = self._client.complete(
                    system_prompt=system_prompt,
                    user_prompt=active_prompt,
                    settings=self._settings,
                )
            token_turns.append((system_prompt + "\n" + active_prompt, raw_response))
            code = extract_python_code(raw_response)
            static_metrics = compute_static_metrics(code)
            pytest_result = run_pytest_for_code(
                code,
                task.test_code,
                timeout_seconds=self._pytest_timeout_seconds,
            )
            gate_failures = self._gate_failures(code, static_metrics, pytest_result)
            attempt = HybridAttempt(
                attempt_index=attempt_index,
                code=code,
                raw_response=raw_response,
                static_metrics=static_metrics,
                pytest=pytest_result,
                gate_failures=gate_failures,
                feedback_prompt=active_prompt if attempt_index > 0 else None,
            )
            attempts.append(attempt)
            if not gate_failures:
                break
            if attempt_index >= self._constraints.max_retries:
                break
            active_prompt = self._build_feedback_prompt(
                task_prompt=user_prompt,
                soft_spec=system_prompt,
                attempt_code=code,
                gate_failures=gate_failures,
                attempt_num=attempt_index + 1,
            )
            feedback_prompts.append(active_prompt)

        final = attempts[-1]
        initial_cc = attempts[0].static_metrics.cyclomatic_complexity_max
        final_cc = final.static_metrics.cyclomatic_complexity_max
        metadata = {
            "constraints": asdict(self._constraints),
            "attempts": [attempt.to_json_dict() for attempt in attempts],
            "feedback_prompts": feedback_prompts,
            "hybrid_retries": max(0, len(attempts) - 1),
            "hybrid_gate_pass": not final.gate_failures,
            "hard_cc_pass": "cc" not in final.gate_failures,
            "hard_nesting_pass": "nesting" not in final.gate_failures,
            "hard_pytest_pass": "pytest" not in final.gate_failures,
            "hybrid_feedback_cc_delta": (
                round(final_cc - initial_cc, 3) if len(attempts) > 1 else None
            ),
            "max_retries_exceeded": bool(final.gate_failures)
            and len(attempts) == self._constraints.max_retries + 1,
        }

        effective_temperature = getattr(
            self._client,
            "last_effective_temperature",
            self._settings.temperature,
        )
        return GenerationResult(
            task_id=task.id,
            mode="hybrid",
            variant="hybrid_generation",
            provider=self._settings.provider,
            model=self._settings.model,
            sample_index=sample_index,
            requested_temperature=self._settings.temperature,
            effective_temperature=effective_temperature,
            entry_point=task.entry_point,
            task=task.to_mapping(),
            oracle_spec=_oracle_spec_from_system_prompt(system_prompt),
            oracle_spec_label="hybrid_oracle",
            code=final.code,
            raw_response=final.raw_response,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            artifact_language="python",
            hybrid=metadata,
            metadata={"token_estimates": token_estimate_summary(token_turns)},
        )

    def _gate_failures(
        self,
        code: str,
        metrics: StaticMetrics,
        pytest_result: PytestResult,
    ) -> dict[str, Any]:
        failures: dict[str, Any] = {}
        if self._constraints.max_cc is not None:
            function_name, branches = _highest_complexity_function(code)
            if metrics.cyclomatic_complexity_max > self._constraints.max_cc:
                failures["cc"] = {
                    "value": metrics.cyclomatic_complexity_max,
                    "threshold": self._constraints.max_cc,
                    "violating_function": function_name,
                    "branches": branches,
                }
        if (
            self._constraints.max_nesting is not None
            and metrics.max_nesting_depth > self._constraints.max_nesting
        ):
            failures["nesting"] = {
                "value": metrics.max_nesting_depth,
                "threshold": self._constraints.max_nesting,
            }
        if self._constraints.require_pytest and not pytest_result.passed:
            output = "\n".join(part for part in (pytest_result.stdout, pytest_result.stderr) if part)
            failures["pytest"] = {
                "passed": False,
                "output": output[:500],
                "timed_out": pytest_result.timed_out,
                "sandbox_error": pytest_result.sandbox_error,
            }
        return failures

    def _build_feedback_prompt(
        self,
        *,
        task_prompt: str,
        soft_spec: str,
        attempt_code: str,
        gate_failures: dict[str, Any],
        attempt_num: int,
    ) -> str:
        feedback_lines = [
            "The previous implementation was rejected by the hard oracle gates.",
            f"Rejected attempt: {attempt_num}",
            "",
            "Original task and soft oracle, unchanged:",
            task_prompt.strip(),
            "",
            "Soft oracle system specification:",
            soft_spec.strip(),
            "",
            "Rejected code:",
            "```python",
            attempt_code.strip(),
            "```",
            "",
            "Structured hard-gate failure report:",
        ]

        if "cc" in gate_failures:
            failure = gate_failures["cc"]
            function_name = failure.get("violating_function") or "the largest function"
            branches = failure.get("branches")
            feedback_lines.extend(
                [
                    (
                        f"- Cyclomatic complexity was {failure['value']}. "
                        f"Target: <= {failure['threshold']}."
                    ),
                    (
                        f"  Decompose {function_name}; it has approximately {branches} "
                        "decision branches. Extract each logical path into a named helper."
                    ),
                ]
            )
        if "nesting" in gate_failures:
            failure = gate_failures["nesting"]
            feedback_lines.extend(
                [
                    (
                        f"- Max nesting depth was {failure['value']}. "
                        f"Target: <= {failure['threshold']}."
                    ),
                    "  Replace nested conditionals with early returns or guard clauses.",
                ]
            )
        if "pytest" in gate_failures:
            failure = gate_failures["pytest"]
            feedback_lines.extend(
                [
                    "- Pytest failed. Relevant output:",
                    str(failure.get("output") or failure.get("sandbox_error") or "")[:500],
                ]
            )

        feedback_lines.extend(
            [
                "",
                "Rewrite the implementation addressing ONLY the specific failures above.",
                "Do not change function signatures or the overall algorithm.",
                "Return only Python code. Do not include markdown prose.",
            ]
        )
        return "\n".join(feedback_lines)


def _highest_complexity_function(code: str) -> tuple[str, int]:
    try:
        blocks = cc_visit(code)
    except Exception:
        return "unknown", 0
    if not blocks:
        return "module", 0
    worst = max(blocks, key=lambda block: int(getattr(block, "complexity", 0)))
    complexity = int(getattr(worst, "complexity", 0))
    return str(getattr(worst, "name", "unknown")), max(0, complexity - 1)


def _oracle_spec_from_system_prompt(system_prompt: str) -> str:
    marker = "Treat the Zen of Python as an informal in-context oracle"
    if marker in system_prompt:
        return system_prompt[system_prompt.index(marker) :].strip()
    custom_marker = "Task-specific informal oracle:"
    if custom_marker in system_prompt:
        return system_prompt.split(custom_marker, 1)[1].strip()
    return system_prompt
