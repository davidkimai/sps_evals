from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from specoracle.config import MAINTENANCE_SYSTEM_PROMPT, MAINTENANCE_USER_TEMPLATE, ModelSettings, Task
from specoracle.evaluator import PytestResult, compute_static_metrics, run_pytest_for_code
from specoracle.generator import LLMClient, extract_python_code


@dataclass(frozen=True)
class StressResult:
    task_id: str
    variant: str
    provider: str
    model: str
    sample_index: int
    requested_temperature: float | None
    effective_temperature: float | None
    oracle_spec: str
    oracle_spec_label: str
    maintenance_provider: str
    maintenance_model: str
    pass_at_1: bool
    duration_seconds: float
    maintenance_token_overhead: int
    maintenance_failure_type: str
    maintenance_failure_detail: str
    context_ablation_pass_at_1: bool | None
    context_ablation_token_overhead: int | None
    context_ablation_failure_type: str | None
    context_ablation_failure_detail: str | None
    pytest: PytestResult | None
    raw_response: str
    code: str
    error: str | None = None

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ChainStepResult:
    step: int
    task_id: str
    variant: str
    provider: str
    model: str
    sample_index: int
    maintenance_provider: str
    maintenance_model: str
    pass_bool: bool
    token_estimate: int
    cc_average: float
    nesting_depth: int
    function_count: int
    elapsed_seconds: float
    accumulated_score: float
    failure_type: str
    failure_detail: str
    raw_response: str
    code: str

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


class SpecArena:
    def __init__(
        self,
        *,
        client: LLMClient,
        settings: ModelSettings,
        pytest_timeout_seconds: float = 10.0,
    ) -> None:
        self._client = client
        self._settings = settings
        self._pytest_timeout_seconds = pytest_timeout_seconds

    def stress_artifact(
        self,
        *,
        artifact_dir: Path,
        task: Task,
        generation_payload: dict[str, Any],
        context_ablation: bool = False,
    ) -> StressResult:
        started = time.monotonic()
        existing_code = (artifact_dir / "solution.py").read_text(encoding="utf-8")
        prompt = _maintenance_prompt(task, existing_code)

        try:
            raw_response, code, pytest_result = self._run_maintenance(
                task=task,
                prompt=prompt,
            )
            passed = pytest_result.passed
            failure_type, failure_detail = _classify_pytest_failure(pytest_result)
            error = None
        except Exception as exc:
            raw_response = locals().get("raw_response", "")
            code = locals().get("code", "")
            pytest_result = None
            passed = False
            failure_type = "maintenance_agent_error"
            failure_detail = str(exc)
            error = str(exc)

        context_passed: bool | None = None
        context_tokens: int | None = None
        context_failure_type: str | None = None
        context_failure_detail: str | None = None
        if context_ablation:
            stub_prompt = _maintenance_prompt(task, _stub_solution_for_task(task, existing_code))
            try:
                context_raw_response, _, context_pytest = self._run_maintenance(
                    task=task,
                    prompt=stub_prompt,
                )
                context_passed = context_pytest.passed
                context_failure_type, context_failure_detail = _classify_pytest_failure(
                    context_pytest
                )
                context_tokens = _estimate_token_overhead(
                    MAINTENANCE_SYSTEM_PROMPT,
                    stub_prompt,
                    context_raw_response,
                )
            except Exception as exc:
                context_passed = False
                context_tokens = _estimate_token_overhead(MAINTENANCE_SYSTEM_PROMPT, stub_prompt)
                context_failure_type = "maintenance_agent_error"
                context_failure_detail = str(exc)

        return StressResult(
            task_id=task.id,
            variant=str(generation_payload["variant"]),
            provider=str(generation_payload["provider"]),
            model=str(generation_payload["model"]),
            sample_index=int(generation_payload.get("sample_index", 0)),
            requested_temperature=_optional_float(generation_payload.get("requested_temperature")),
            effective_temperature=_optional_float(generation_payload.get("effective_temperature")),
            oracle_spec=str(generation_payload.get("oracle_spec") or ""),
            oracle_spec_label=str(generation_payload.get("oracle_spec_label") or ""),
            maintenance_provider=self._settings.provider,
            maintenance_model=self._settings.model,
            pass_at_1=passed,
            duration_seconds=round(time.monotonic() - started, 3),
            maintenance_token_overhead=_estimate_token_overhead(
                MAINTENANCE_SYSTEM_PROMPT,
                prompt,
                raw_response,
            ),
            maintenance_failure_type=failure_type,
            maintenance_failure_detail=failure_detail,
            context_ablation_pass_at_1=context_passed,
            context_ablation_token_overhead=context_tokens,
            context_ablation_failure_type=context_failure_type,
            context_ablation_failure_detail=context_failure_detail,
            pytest=pytest_result,
            raw_response=raw_response,
            code=code,
            error=error,
        )

    def _run_maintenance(
        self,
        *,
        task: Task,
        prompt: str,
    ) -> tuple[str, str, PytestResult]:
        if self._settings.provider == "mock" and task.mock_day2_solution:
            raw_response = task.mock_day2_solution
        else:
            raw_response = self._client.complete(
                system_prompt=MAINTENANCE_SYSTEM_PROMPT,
                user_prompt=prompt,
                settings=self._settings,
            )
        code = extract_python_code(raw_response)
        pytest_result = run_pytest_for_code(
            code,
            task.day2_test_code,
            timeout_seconds=self._pytest_timeout_seconds,
        )
        return raw_response, code, pytest_result

    def stress_run_dir(
        self,
        *,
        run_dir: Path,
        task_map: dict[str, Task] | None = None,
        context_ablation: bool = False,
    ) -> list[StressResult]:
        results: list[StressResult] = []
        for generation_path in sorted(run_dir.rglob("generation.json")):
            payload = json.loads(generation_path.read_text(encoding="utf-8"))
            task = _task_for_generation(payload, task_map)
            existing = load_existing_stress_result(
                artifact_dir=generation_path.parent,
                generation_payload=payload,
                settings=self._settings,
                context_ablation=context_ablation,
            )
            if existing is not None:
                results.append(existing)
                continue
            result = self.stress_artifact(
                artifact_dir=generation_path.parent,
                task=task,
                generation_payload=payload,
                context_ablation=context_ablation,
            )
            write_stress_result(result, generation_path.parent)
            results.append(result)
        return results

    def chain_run_dir(
        self,
        *,
        run_dir: Path,
        task_map: dict[str, Task] | None = None,
        chain_depth: int = 1,
    ) -> list[ChainStepResult]:
        if chain_depth <= 1:
            return []

        results: list[ChainStepResult] = []
        for generation_path in sorted(run_dir.rglob("generation.json")):
            payload = json.loads(generation_path.read_text(encoding="utf-8"))
            task = _task_for_generation(payload, task_map)
            existing = load_existing_chain_results(
                artifact_dir=generation_path.parent,
                generation_payload=payload,
                settings=self._settings,
                chain_depth=chain_depth,
            )
            if existing is not None:
                results.extend(existing)
                continue
            chain_results = self.chain_artifact(
                artifact_dir=generation_path.parent,
                task=task,
                generation_payload=payload,
                chain_depth=chain_depth,
            )
            write_chain_results(chain_results, generation_path.parent)
            results.extend(chain_results)
        return results

    def chain_artifact(
        self,
        *,
        artifact_dir: Path,
        task: Task,
        generation_payload: dict[str, Any],
        chain_depth: int,
    ) -> list[ChainStepResult]:
        if chain_depth <= 1:
            return []

        steps: list[ChainStepResult] = []
        accumulated_score = 0.0

        stress_path = artifact_dir / "stress.json"
        if stress_path.exists():
            stress = stress_result_from_mapping(json.loads(stress_path.read_text(encoding="utf-8")))
            step_one_code = stress.code
            step_one_raw = stress.raw_response
            step_one_pytest = stress.pytest
            step_one_passed = stress.pass_at_1
            step_one_failure_type = stress.maintenance_failure_type
            step_one_failure_detail = stress.maintenance_failure_detail
            step_one_elapsed = stress.duration_seconds
            step_one_tokens = stress.maintenance_token_overhead
        else:
            started = time.monotonic()
            step_one_raw, step_one_code, step_one_pytest = self._run_maintenance(
                task=task,
                prompt=_maintenance_prompt(
                    task,
                    (artifact_dir / "solution.py").read_text(encoding="utf-8"),
                ),
            )
            step_one_passed = step_one_pytest.passed
            step_one_failure_type, step_one_failure_detail = _classify_pytest_failure(
                step_one_pytest
            )
            step_one_elapsed = round(time.monotonic() - started, 3)
            step_one_tokens = _estimate_token_overhead(
                MAINTENANCE_SYSTEM_PROMPT,
                _maintenance_prompt(
                    task,
                    (artifact_dir / "solution.py").read_text(encoding="utf-8"),
                ),
                step_one_raw,
            )
        step_one = _chain_step_from_code(
            step=1,
            task=task,
            generation_payload=generation_payload,
            settings=self._settings,
            code=step_one_code,
            raw_response=step_one_raw,
            pytest_result=step_one_pytest,
            passed=step_one_passed,
            token_estimate=step_one_tokens,
            elapsed_seconds=step_one_elapsed,
            failure_type=step_one_failure_type,
            failure_detail=step_one_failure_detail,
            accumulated_score=accumulated_score,
        )
        accumulated_score = step_one.accumulated_score
        steps.append(step_one)

        current_code = step_one_code
        for step in range(2, chain_depth + 1):
            prompt = _chain_prompt(task=task, code=current_code, step=step)
            started = time.monotonic()
            try:
                raw_response, code, pytest_result = self._run_chain_step(
                    task=task,
                    prompt=prompt,
                    fallback_code=current_code,
                )
                passed = pytest_result.passed
                failure_type, failure_detail = _classify_pytest_failure(pytest_result)
            except Exception as exc:
                raw_response = ""
                code = current_code
                pytest_result = None
                passed = False
                failure_type = "maintenance_agent_error"
                failure_detail = str(exc)
            token_estimate = _estimate_token_overhead(
                MAINTENANCE_SYSTEM_PROMPT,
                prompt,
                raw_response,
            )
            result = _chain_step_from_code(
                step=step,
                task=task,
                generation_payload=generation_payload,
                settings=self._settings,
                code=code,
                raw_response=raw_response,
                pytest_result=pytest_result,
                passed=passed,
                token_estimate=token_estimate,
                elapsed_seconds=round(time.monotonic() - started, 3),
                failure_type=failure_type,
                failure_detail=failure_detail,
                accumulated_score=accumulated_score,
            )
            accumulated_score = result.accumulated_score
            steps.append(result)
            current_code = code
        return steps

    def _run_chain_step(
        self,
        *,
        task: Task,
        prompt: str,
        fallback_code: str,
    ) -> tuple[str, str, PytestResult]:
        if self._settings.provider == "mock":
            raw_response = fallback_code
        else:
            raw_response = self._client.complete(
                system_prompt=MAINTENANCE_SYSTEM_PROMPT,
                user_prompt=prompt,
                settings=self._settings,
            )
        code = extract_python_code(raw_response)
        pytest_result = run_pytest_for_code(
            code,
            task.day2_test_code,
            timeout_seconds=self._pytest_timeout_seconds,
        )
        return raw_response, code, pytest_result


def load_existing_stress_result(
    *,
    artifact_dir: Path,
    generation_payload: dict[str, Any],
    settings: ModelSettings,
    context_ablation: bool = False,
) -> StressResult | None:
    stress_path = artifact_dir / "stress.json"
    day2_solution_path = artifact_dir / "day2_solution.py"
    stress_exists = stress_path.exists()
    day2_solution_exists = day2_solution_path.exists()
    if not stress_exists and not day2_solution_exists:
        return None
    if stress_exists != day2_solution_exists:
        raise RuntimeError(
            f"partial stress artifact in {artifact_dir}: "
            "expected both stress.json and day2_solution.py"
        )

    try:
        payload = json.loads(stress_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"malformed stress artifact: {stress_path}") from exc

    result = stress_result_from_mapping(payload)
    expected_key = _generation_key(generation_payload)
    actual_key = (
        result.task_id,
        result.variant,
        result.provider,
        result.model,
        result.sample_index,
    )
    if actual_key != expected_key:
        raise RuntimeError(
            f"stress artifact key mismatch for {stress_path}: "
            f"expected {expected_key}, found {actual_key}"
        )
    expected_maintenance = (settings.provider, settings.model)
    actual_maintenance = (result.maintenance_provider, result.maintenance_model)
    if actual_maintenance != expected_maintenance:
        raise RuntimeError(
            f"stress artifact maintenance model mismatch for {stress_path}: "
            f"expected {expected_maintenance}, found {actual_maintenance}"
        )
    if context_ablation and result.context_ablation_pass_at_1 is None:
        raise RuntimeError(
            f"stress artifact missing context ablation fields for {stress_path}; "
            "rerun without --context-ablation or remove the partial stress artifact"
        )

    day2_code = day2_solution_path.read_text(encoding="utf-8").rstrip("\n")
    if result.code.rstrip("\n") != day2_code:
        raise RuntimeError(
            f"stress artifact code mismatch between {stress_path} and {day2_solution_path}"
        )
    return result


def write_stress_result(result: StressResult, artifact_dir: Path) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "day2_solution.py").write_text(result.code + "\n", encoding="utf-8")
    (artifact_dir / "stress.json").write_text(
        json.dumps(result.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_existing_chain_results(
    *,
    artifact_dir: Path,
    generation_payload: dict[str, Any],
    settings: ModelSettings,
    chain_depth: int,
) -> list[ChainStepResult] | None:
    chain_path = artifact_dir / "chain_results.json"
    if not chain_path.exists():
        return None
    try:
        payload = json.loads(chain_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"malformed chain artifact: {chain_path}") from exc
    steps_payload = payload.get("steps")
    if not isinstance(steps_payload, list):
        raise RuntimeError(f"malformed chain artifact: {chain_path}")
    if len(steps_payload) != chain_depth:
        raise RuntimeError(
            f"chain artifact depth mismatch for {chain_path}: "
            f"expected {chain_depth}, found {len(steps_payload)}"
        )
    expected_key = _generation_key(generation_payload)
    results = [chain_step_from_mapping(step) for step in steps_payload]
    expected_maintenance = (settings.provider, settings.model)
    for result in results:
        actual_key = (
            result.task_id,
            result.variant,
            result.provider,
            result.model,
            result.sample_index,
        )
        if actual_key != expected_key:
            raise RuntimeError(
                f"chain artifact key mismatch for {chain_path}: "
                f"expected {expected_key}, found {actual_key}"
            )
        actual_maintenance = (result.maintenance_provider, result.maintenance_model)
        if actual_maintenance != expected_maintenance:
            raise RuntimeError(
                f"chain artifact maintenance model mismatch for {chain_path}: "
                f"expected {expected_maintenance}, found {actual_maintenance}"
            )
    return results


def write_chain_results(results: list[ChainStepResult], artifact_dir: Path) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "chain_results.json").write_text(
        json.dumps(
            {"steps": [result.to_json_dict() for result in results]},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def chain_step_from_mapping(payload: dict[str, Any]) -> ChainStepResult:
    return ChainStepResult(
        step=int(payload["step"]),
        task_id=str(payload["task_id"]),
        variant=str(payload["variant"]),
        provider=str(payload["provider"]),
        model=str(payload["model"]),
        sample_index=int(payload.get("sample_index", 0)),
        maintenance_provider=str(payload["maintenance_provider"]),
        maintenance_model=str(payload["maintenance_model"]),
        pass_bool=bool(payload["pass_bool"]),
        token_estimate=int(payload["token_estimate"]),
        cc_average=float(payload["cc_average"]),
        nesting_depth=int(payload["nesting_depth"]),
        function_count=int(payload["function_count"]),
        elapsed_seconds=float(payload["elapsed_seconds"]),
        accumulated_score=float(payload["accumulated_score"]),
        failure_type=str(payload.get("failure_type") or ""),
        failure_detail=str(payload.get("failure_detail") or ""),
        raw_response=str(payload.get("raw_response") or ""),
        code=str(payload.get("code") or ""),
    )


def stress_result_from_mapping(payload: dict[str, Any]) -> StressResult:
    pytest_payload = payload.get("pytest")
    if pytest_payload:
        pytest_payload = dict(pytest_payload)
        pytest_payload.setdefault("sandbox", "unknown")
        pytest_payload.setdefault("sandbox_error", None)
    pytest_result = PytestResult(**pytest_payload) if pytest_payload else None
    pass_at_1 = bool(payload["pass_at_1"])
    return StressResult(
        task_id=str(payload["task_id"]),
        variant=str(payload["variant"]),
        provider=str(payload["provider"]),
        model=str(payload["model"]),
        sample_index=int(payload.get("sample_index", 0)),
        requested_temperature=_optional_float(payload.get("requested_temperature")),
        effective_temperature=_optional_float(payload.get("effective_temperature")),
        oracle_spec=str(payload.get("oracle_spec") or ""),
        oracle_spec_label=str(payload.get("oracle_spec_label") or ""),
        maintenance_provider=str(payload["maintenance_provider"]),
        maintenance_model=str(payload["maintenance_model"]),
        pass_at_1=pass_at_1,
        duration_seconds=float(payload["duration_seconds"]),
        maintenance_token_overhead=int(
            payload.get("maintenance_token_overhead", payload.get("token_cost", 0))
        ),
        maintenance_failure_type=str(
            payload.get("maintenance_failure_type") or ("none" if pass_at_1 else "unknown")
        ),
        maintenance_failure_detail=str(payload.get("maintenance_failure_detail") or ""),
        context_ablation_pass_at_1=(
            bool(payload["context_ablation_pass_at_1"])
            if payload.get("context_ablation_pass_at_1") is not None
            else None
        ),
        context_ablation_token_overhead=(
            int(payload["context_ablation_token_overhead"])
            if payload.get("context_ablation_token_overhead") is not None
            else None
        ),
        context_ablation_failure_type=(
            str(payload["context_ablation_failure_type"])
            if payload.get("context_ablation_failure_type") is not None
            else None
        ),
        context_ablation_failure_detail=(
            str(payload["context_ablation_failure_detail"])
            if payload.get("context_ablation_failure_detail") is not None
            else None
        ),
        pytest=pytest_result,
        raw_response=str(payload.get("raw_response") or ""),
        code=str(payload.get("code") or ""),
        error=str(payload["error"]) if payload.get("error") is not None else None,
    )


def _task_for_generation(
    payload: dict[str, Any],
    task_map: dict[str, Task] | None,
) -> Task:
    task_id = str(payload["task_id"])
    if task_map is not None and task_id in task_map:
        return task_map[task_id]
    if isinstance(payload.get("task"), dict):
        return Task.from_mapping(payload["task"])
    raise ValueError(
        f"generation artifact for task {task_id!r} does not include a task snapshot; "
        "rerun generation or pass --dataset to the stress command"
    )


def _generation_key(payload: dict[str, Any]) -> tuple[str, str, str, str, int]:
    return (
        str(payload["task_id"]),
        str(payload["variant"]),
        str(payload["provider"]),
        str(payload["model"]),
        int(payload.get("sample_index", 0)),
    )


def _estimate_token_overhead(*texts: str) -> int:
    chars = sum(len(text) for text in texts)
    return max(1, (chars + 3) // 4)


def _maintenance_prompt(task: Task, code: str) -> str:
    return MAINTENANCE_USER_TEMPLATE.format(
        task_id=task.id,
        entry_point=task.entry_point,
        prompt=task.prompt.strip(),
        code=code,
        day2_prompt=task.day2_prompt.strip(),
    )


def _chain_prompt(task: Task, code: str, step: int) -> str:
    if step == 2:
        instruction = (
            "The code above works. Refactor it: extract any function longer than "
            "15 lines into named helpers. Do not change behavior."
        )
    else:
        instruction = (
            "Add input validation and error handling to all public functions. "
            "Do not change the core algorithm."
        )
    return f"""\
Task id: {task.id}
Entry point: {task.entry_point}

Original functional requirements:
{task.prompt.strip()}

Current solution.py:
```python
{code}
```

Chained maintenance step {step}:
{instruction}

Maintenance instructions:
- Return a complete replacement Python module.
- Preserve original and Day 2 behavior.
- Keep imports standard-library only unless the task explicitly permits otherwise.
- Prefer small, auditable edits.
"""


def _chain_step_from_code(
    *,
    step: int,
    task: Task,
    generation_payload: dict[str, Any],
    settings: ModelSettings,
    code: str,
    raw_response: str,
    pytest_result: PytestResult | None,
    passed: bool,
    token_estimate: int,
    elapsed_seconds: float,
    failure_type: str,
    failure_detail: str,
    accumulated_score: float,
) -> ChainStepResult:
    metrics = compute_static_metrics(code)
    next_accumulated = accumulated_score + (
        metrics.cyclomatic_complexity_average * token_estimate
    )
    return ChainStepResult(
        step=step,
        task_id=task.id,
        variant=str(generation_payload["variant"]),
        provider=str(generation_payload["provider"]),
        model=str(generation_payload["model"]),
        sample_index=int(generation_payload.get("sample_index", 0)),
        maintenance_provider=settings.provider,
        maintenance_model=settings.model,
        pass_bool=passed,
        token_estimate=token_estimate,
        cc_average=metrics.cyclomatic_complexity_average,
        nesting_depth=metrics.max_nesting_depth,
        function_count=metrics.function_count,
        elapsed_seconds=elapsed_seconds,
        accumulated_score=round(next_accumulated, 3),
        failure_type=failure_type,
        failure_detail=failure_detail,
        raw_response=raw_response,
        code=code,
    )


def _stub_solution_for_task(task: Task, existing_code: str) -> str:
    if f"class {task.entry_point}" in existing_code:
        return f"class {task.entry_point}:\n    pass\n"
    return f"def {task.entry_point}(*args, **kwargs):\n    pass\n"


def _optional_float(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    return float(value)


def _classify_pytest_failure(result: PytestResult) -> tuple[str, str]:
    if result.passed:
        return "none", ""
    if result.sandbox_error:
        return "sandbox_error", result.sandbox_error
    if result.timed_out:
        return "timeout", "pytest subprocess exceeded timeout"

    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    lowered = output.lower()
    if "syntaxerror" in lowered:
        return "syntax_error", _first_relevant_line(output, "SyntaxError")
    if "assertionerror" in lowered or "assert " in lowered or "assertion failed" in lowered:
        return "assertion_failure", _first_relevant_line(output, "assert")
    return "runtime_error", _first_relevant_line(output, "E   ") or output.strip()[:500]


def _first_relevant_line(output: str, needle: str) -> str:
    for line in output.splitlines():
        if needle in line:
            return line.strip()
    return output.strip()[:500]
