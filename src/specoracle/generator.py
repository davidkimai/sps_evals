from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from typing import Any, Protocol

from specoracle.config import (
    DAFNY_GENERATION_USER_TEMPLATE,
    GENERATION_USER_TEMPLATE,
    GenerationMode,
    ModelSettings,
    NEUTRAL_STYLE_SPEC,
    OracleSource,
    Task,
    oracle_spec_for_task,
    oracle_spec_label_for_task,
    system_prompt_for_mode,
    variant_name,
)
from specoracle.skills_registry import get_skill, get_skill_tool_schema, render_skill_catalog


class LLMClient(Protocol):
    def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        settings: ModelSettings,
    ) -> str:
        """Return a single text completion for a system/user prompt pair."""


@dataclass(frozen=True)
class ToolCall:
    name: str
    input: dict[str, Any]
    id: str | None = None


@dataclass(frozen=True)
class ToolCompletion:
    text: str
    tool_calls: tuple[ToolCall, ...] = ()
    raw_response: str = ""


@dataclass(frozen=True)
class GenerationResult:
    task_id: str
    mode: GenerationMode
    variant: str
    provider: str
    model: str
    sample_index: int
    requested_temperature: float
    effective_temperature: float | None
    entry_point: str
    task: dict[str, Any]
    oracle_spec: str
    oracle_spec_label: str
    code: str
    raw_response: str
    system_prompt: str
    user_prompt: str
    artifact_language: str = "python"
    hybrid: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


class OpenAIClient:
    def __init__(self, api_key: str | None = None) -> None:
        from openai import OpenAI

        max_retries = int(os.getenv("SPECORACLE_OPENAI_MAX_RETRIES", "2"))
        self._client = OpenAI(api_key=api_key, max_retries=max_retries)
        self.last_effective_temperature: float | None = None
        self.last_usage: dict[str, int] | None = None

    def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        settings: ModelSettings,
    ) -> str:
        request = {
            "model": settings.model,
            "instructions": system_prompt,
            "input": user_prompt,
            "temperature": settings.temperature,
            "max_output_tokens": settings.max_tokens,
            "timeout": settings.timeout_seconds,
        }
        self.last_effective_temperature = settings.temperature
        try:
            response = self._client.responses.create(**request)
        except Exception as exc:
            if not _is_unsupported_temperature_error(exc):
                raise
            if settings.require_temperature:
                raise RuntimeError(
                    f"{settings.model} rejected temperature={settings.temperature}; "
                    "cannot claim independent samples with --require-temperature"
                ) from exc
            request.pop("temperature", None)
            self.last_effective_temperature = None
            response = self._client.responses.create(**request)
        self.last_usage = _extract_usage(response)
        return _extract_openai_text(response)


class AnthropicClient:
    def __init__(self, api_key: str | None = None) -> None:
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise RuntimeError(
                "Anthropic support requires the optional dependency: "
                "python -m pip install 'specoracle[anthropic]'"
            ) from exc

        self._client = Anthropic(api_key=api_key)
        self.last_effective_temperature: float | None = None
        self.last_usage: dict[str, int] | None = None

    def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        settings: ModelSettings,
    ) -> str:
        self.last_effective_temperature = settings.temperature
        response = self._client.messages.create(
            model=settings.model,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            timeout=settings.timeout_seconds,
        )
        self.last_usage = _extract_usage(response)
        parts: list[str] = []
        for block in getattr(response, "content", []):
            text = getattr(block, "text", None)
            if text:
                parts.append(str(text))
        return "\n".join(parts).strip()

    def complete_with_tools(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        tools: list[dict[str, Any]],
        settings: ModelSettings,
    ) -> ToolCompletion:
        self.last_effective_temperature = settings.temperature
        response = self._client.messages.create(
            model=settings.model,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            tools=tools,
            timeout=settings.timeout_seconds,
        )
        self.last_usage = _extract_usage(response)
        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for block in getattr(response, "content", []):
            block_type = getattr(block, "type", "")
            if block_type == "text" and getattr(block, "text", None):
                text_parts.append(str(block.text))
            elif block_type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        name=str(getattr(block, "name", "")),
                        input=dict(getattr(block, "input", {}) or {}),
                        id=getattr(block, "id", None),
                    )
                )
        return ToolCompletion(
            text="\n".join(text_parts).strip(),
            tool_calls=tuple(tool_calls),
            raw_response=str(response),
        )


class GoogleClient:
    def __init__(self, api_key: str | None = None) -> None:
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError(
                "Google/Gemini support requires the optional dependency: "
                "python -m pip install 'specoracle[google]'"
            ) from exc

        self._client = genai.Client(api_key=api_key)
        self.last_effective_temperature: float | None = None
        self.last_usage: dict[str, int] | None = None

    def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        settings: ModelSettings,
    ) -> str:
        try:
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError(
                "Google/Gemini support requires the optional dependency: "
                "python -m pip install 'specoracle[google]'"
            ) from exc

        self.last_effective_temperature = settings.temperature
        response = self._client.models.generate_content(
            model=settings.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=settings.temperature,
                max_output_tokens=settings.max_tokens,
            ),
        )
        self.last_usage = _extract_usage(response)
        return _extract_google_text(response)


class MockLLMClient:
    """Offline client for smoke tests; not a research model."""

    last_effective_temperature: float | None = None
    last_usage: dict[str, int] | None = None
    tool_call_count = 0

    def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        settings: ModelSettings,
    ) -> str:
        self.last_effective_temperature = settings.temperature
        if "strict JSON" in system_prompt or '"score"' in user_prompt:
            return (
                '{"score": 8, "rationale": "Readable, explicit, and locally auditable.", '
                '"strengths": ["simple control flow"], "weaknesses": ["mock judgment"]}'
            )
        return "def solution(*args, **kwargs):\n    raise NotImplementedError('mock task fixture missing')\n"

    def complete_with_tools(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        tools: list[dict[str, Any]],
        settings: ModelSettings,
    ) -> ToolCompletion:
        self.last_effective_temperature = settings.temperature
        self.tool_call_count += 1
        return ToolCompletion(
            text="",
            tool_calls=(ToolCall(name="get_skill", input={"skill_id": "dafny"}, id="mock_tool_0"),),
            raw_response='{"tool_call": {"name": "get_skill", "input": {"skill_id": "dafny"}}}',
        )


def build_llm_client(settings: ModelSettings) -> LLMClient:
    if settings.provider == "mock":
        return MockLLMClient()

    api_key = os.getenv(settings.api_key_env)
    if not api_key:
        raise RuntimeError(
            f"{settings.provider} provider requires ${settings.api_key_env}; "
            "set it in your shell or use --provider mock for an offline smoke run"
        )

    if settings.provider == "openai":
        return OpenAIClient(api_key=api_key)
    if settings.provider == "anthropic":
        return AnthropicClient(api_key=api_key)
    if settings.provider == "google":
        return GoogleClient(api_key=api_key)
    raise ValueError(f"unknown provider: {settings.provider}")


class SpecOracleGenerator:
    def __init__(self, client: LLMClient, settings: ModelSettings) -> None:
        self._client = client
        self._settings = settings

    @property
    def settings(self) -> ModelSettings:
        return self._settings

    @property
    def client(self) -> LLMClient:
        return self._client

    def baseline_generation(self, task: Task) -> GenerationResult:
        return self.generate(task, mode="baseline")

    def oracle_generation(self, task: Task) -> GenerationResult:
        return self.generate(task, mode="oracle")

    def karpathy_oracle_generation(self, task: Task) -> GenerationResult:
        return self.generate(task, mode="oracle_karpathy")

    def dafny_oracle_generation(self, task: Task) -> GenerationResult:
        return self.generate(task, mode="oracle_dafny")

    def neutral_style_generation(self, task: Task) -> GenerationResult:
        return self.generate(task, mode="neutral_style")

    def modular_discovery_generation(self, task: Task) -> GenerationResult:
        return self.generate(task, mode="modular_discovery")

    def generate(
        self,
        task: Task,
        *,
        mode: GenerationMode,
        sample_index: int = 0,
    ) -> GenerationResult:
        if mode == "modular_discovery":
            return self._generate_modular_discovery(task, sample_index=sample_index)

        system_prompt = system_prompt_for_mode(mode, task=task)
        template = DAFNY_GENERATION_USER_TEMPLATE if mode == "oracle_dafny" else GENERATION_USER_TEMPLATE
        user_prompt = template.format(
            task_id=task.id,
            entry_point=task.entry_point,
            prompt=task.prompt.strip(),
        )

        if self._settings.provider == "mock" and task.mock_solution:
            raw_response = task.mock_solution
        else:
            raw_response = self._client.complete(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                settings=self._settings,
            )

        artifact_language = "dafny" if mode == "oracle_dafny" else "python"
        code = extract_dafny_code(raw_response) if artifact_language == "dafny" else extract_python_code(raw_response)
        effective_temperature = getattr(
            self._client,
            "last_effective_temperature",
            self._settings.temperature,
        )
        oracle_source = _oracle_source_for_mode(mode)
        active_spec = (
            NEUTRAL_STYLE_SPEC
            if mode == "neutral_style"
            else oracle_spec_for_task(task, source=oracle_source)
        )
        active_spec_label = (
            "neutral_style"
            if mode == "neutral_style"
            else oracle_spec_label_for_task(task, source=oracle_source)
        )
        return GenerationResult(
            task_id=task.id,
            mode=mode,
            variant=variant_name(mode),
            provider=self._settings.provider,
            model=self._settings.model,
            sample_index=sample_index,
            requested_temperature=self._settings.temperature,
            effective_temperature=effective_temperature,
            entry_point=task.entry_point,
            task=task.to_mapping(),
            oracle_spec=active_spec,
            oracle_spec_label=active_spec_label,
            code=code,
            raw_response=raw_response,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            artifact_language=artifact_language,
            metadata={
                "token_estimates": token_estimate_summary(
                    [(system_prompt + "\n" + user_prompt, raw_response)]
                )
            },
        )

    def _generate_modular_discovery(
        self,
        task: Task,
        *,
        sample_index: int,
    ) -> GenerationResult:
        system_prompt = system_prompt_for_mode("modular_discovery", task=task)
        base_user_prompt = GENERATION_USER_TEMPLATE.format(
            task_id=task.id,
            entry_point=task.entry_point,
            prompt=task.prompt.strip(),
        )
        tool_schema = get_skill_tool_schema()
        discovery_prompt = (
            f"{base_user_prompt}\n\n"
            "Available skills:\n"
            f"{render_skill_catalog()}\n\n"
            "Use the get_skill tool to load the most relevant skill before solving. "
            "If none apply, return final Python code directly."
        )

        first = _complete_with_tools_if_supported(
            self._client,
            system_prompt=system_prompt,
            user_prompt=discovery_prompt,
            tools=[tool_schema],
            settings=self._settings,
        )
        selected_skill_ids: list[str] = []
        tool_results: list[str] = []
        for tool_call in first.tool_calls:
            if tool_call.name != "get_skill":
                continue
            skill_id = str(tool_call.input.get("skill_id", ""))
            skill = get_skill(skill_id)
            selected_skill_ids.append(skill.skill_id)
            tool_results.append(
                "TOOL RESULT get_skill(skill_id={skill_id!r})\n"
                "{content}".format(skill_id=skill.skill_id, content=skill.content)
            )

        selected_dafny = "dafny" in selected_skill_ids
        if tool_results:
            final_instruction = (
                "Return the final complete Dafny source only."
                if selected_dafny
                else "Return the final complete Python module only."
            )
            final_prompt = (
                f"{base_user_prompt}\n\n"
                + "\n\n".join(tool_results)
                + "\n\nUse the loaded skill content as the active oracle. "
                + final_instruction
            )
            raw_response = self._client.complete(
                system_prompt=system_prompt,
                user_prompt=final_prompt,
                settings=self._settings,
            )
            user_prompt = final_prompt
            raw_for_artifact = (
                "FIRST TURN:\n"
                f"{first.raw_response or first.text}\n\nSECOND TURN:\n{raw_response}"
            )
        else:
            raw_response = first.text
            user_prompt = discovery_prompt
            raw_for_artifact = first.raw_response or first.text

        code = extract_dafny_code(raw_response) if selected_dafny else extract_python_code(raw_response)
        if selected_dafny and _looks_like_python_source(code):
            artifact_language = "python"
            dafny_hint = "language_mismatch"
        elif selected_dafny:
            artifact_language = "dafny"
            dafny_hint = None if _looks_like_dafny_source(code) else "invalid_dafny_output"
        else:
            artifact_language = "python"
            dafny_hint = None
        effective_temperature = getattr(
            self._client,
            "last_effective_temperature",
            self._settings.temperature,
        )
        active_spec = (
            "\n\n".join(tool_results)
            if tool_results
            else "No modular discovery skill was selected."
        )
        return GenerationResult(
            task_id=task.id,
            mode="modular_discovery",
            variant=variant_name("modular_discovery"),
            provider=self._settings.provider,
            model=self._settings.model,
            sample_index=sample_index,
            requested_temperature=self._settings.temperature,
            effective_temperature=effective_temperature,
            entry_point=task.entry_point,
            task=task.to_mapping(),
            oracle_spec=active_spec,
            oracle_spec_label="modular_discovery",
            code=code,
            raw_response=raw_for_artifact,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            artifact_language=artifact_language,
            metadata={
                "modular_discovery": {
                    "selected_skill_ids": selected_skill_ids,
                    "available_skill_ids": tool_schema["input_schema"]["properties"]["skill_id"][
                        "enum"
                    ],
                    "tool_call_count": len(first.tool_calls),
                    "dafny_status_hint": dafny_hint,
                }
                ,
                "token_estimates": token_estimate_summary(
                    (
                        [
                            (system_prompt + "\n" + discovery_prompt, first.raw_response or first.text),
                            (system_prompt + "\n" + user_prompt, raw_response),
                        ]
                        if tool_results
                        else [(system_prompt + "\n" + discovery_prompt, raw_response)]
                    )
                ),
            },
        )


_PYTHON_FENCE = re.compile(r"```(?:python|py)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)
_DAFNY_FENCE = re.compile(r"```(?:dafny|dfy)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)


def extract_python_code(text: str) -> str:
    matches = _PYTHON_FENCE.findall(text)
    if matches:
        return max((match.strip() for match in matches), key=len)
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        first = lines[0].strip().lower()
        if first in {"```", "```python", "```py"}:
            body = "\n".join(lines[1:]).strip()
            return body.removesuffix("```").strip()
    return stripped


def extract_dafny_code(text: str) -> str:
    matches = _DAFNY_FENCE.findall(text)
    if matches:
        return max((match.strip() for match in matches), key=len)
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        first = lines[0].strip().lower()
        if first in {"```", "```dafny", "```dfy"}:
            body = "\n".join(lines[1:]).strip()
            return body.removesuffix("```").strip()
    return stripped


def generation_result_from_mapping(
    payload: dict[str, Any],
    *,
    code: str | None = None,
) -> GenerationResult:
    return GenerationResult(
        task_id=str(payload["task_id"]),
        mode=_as_generation_mode(payload["mode"]),
        variant=str(payload["variant"]),
        provider=str(payload["provider"]),
        model=str(payload["model"]),
        sample_index=int(payload.get("sample_index", 0)),
        requested_temperature=float(payload["requested_temperature"]),
        effective_temperature=_optional_float(payload.get("effective_temperature")),
        entry_point=str(payload["entry_point"]),
        task=dict(payload.get("task") or {}),
        oracle_spec=str(payload.get("oracle_spec") or ""),
        oracle_spec_label=str(payload.get("oracle_spec_label") or ""),
        code=code if code is not None else str(payload.get("code") or ""),
        raw_response=str(payload.get("raw_response") or ""),
        system_prompt=str(payload.get("system_prompt") or ""),
        user_prompt=str(payload.get("user_prompt") or ""),
        artifact_language=str(payload.get("artifact_language") or "python"),
        hybrid=dict(payload["hybrid"]) if isinstance(payload.get("hybrid"), dict) else None,
        metadata=(
            dict(payload["metadata"]) if isinstance(payload.get("metadata"), dict) else None
        ),
    )


def _extract_openai_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return str(output_text).strip()

    parts: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                parts.append(str(text))
    return "\n".join(parts).strip()


def _extract_google_text(response: Any) -> str:
    text = getattr(response, "text", None)
    if text:
        return str(text).strip()

    parts: list[str] = []
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", []) or []:
            part_text = getattr(part, "text", None)
            if part_text:
                parts.append(str(part_text))
    return "\n".join(parts).strip()


def _extract_usage(response: Any) -> dict[str, int] | None:
    usage = getattr(response, "usage", None) or getattr(response, "usage_metadata", None)
    if usage is None:
        return None
    input_tokens = (
        getattr(usage, "input_tokens", None)
        or getattr(usage, "prompt_tokens", None)
        or getattr(usage, "prompt_token_count", None)
    )
    output_tokens = (
        getattr(usage, "output_tokens", None)
        or getattr(usage, "completion_tokens", None)
        or getattr(usage, "candidates_token_count", None)
    )
    total_tokens = getattr(usage, "total_tokens", None) or getattr(usage, "total_token_count", None)
    result: dict[str, int] = {}
    if isinstance(input_tokens, int):
        result["input_tokens"] = input_tokens
    if isinstance(output_tokens, int):
        result["output_tokens"] = output_tokens
    if isinstance(total_tokens, int):
        result["total_tokens"] = total_tokens
    if "total_tokens" not in result and {"input_tokens", "output_tokens"} <= set(result):
        result["total_tokens"] = result["input_tokens"] + result["output_tokens"]
    return result or None


def _is_unsupported_temperature_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "unsupported parameter" in message and "temperature" in message


def _complete_with_tools_if_supported(
    client: LLMClient,
    *,
    system_prompt: str,
    user_prompt: str,
    tools: list[dict[str, Any]],
    settings: ModelSettings,
) -> ToolCompletion:
    complete_with_tools = getattr(client, "complete_with_tools", None)
    if callable(complete_with_tools):
        return complete_with_tools(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            tools=tools,
            settings=settings,
        )

    fallback_prompt = (
        f"{user_prompt}\n\n"
        "Tool calling is not available in this client. If you need a skill, return "
        "strict JSON in this shape and no prose: "
        '{"tool_call":{"name":"get_skill","input":{"skill_id":"dafny"}}}. '
        "Otherwise return final Python code."
    )
    text = client.complete(
        system_prompt=system_prompt,
        user_prompt=fallback_prompt,
        settings=settings,
    )
    return ToolCompletion(
        text=text,
        tool_calls=_extract_text_tool_calls(text),
        raw_response=text,
    )


def _extract_text_tool_calls(text: str) -> tuple[ToolCall, ...]:
    stripped = text.strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start < 0 or end < start:
        return ()
    try:
        payload = json.loads(stripped[start : end + 1])
    except json.JSONDecodeError:
        return ()
    raw_call = payload.get("tool_call") if isinstance(payload, dict) else None
    if not isinstance(raw_call, dict):
        return ()
    name = raw_call.get("name")
    raw_input = raw_call.get("input")
    if name != "get_skill" or not isinstance(raw_input, dict):
        return ()
    return (ToolCall(name="get_skill", input=dict(raw_input)),)


def _as_generation_mode(value: Any) -> GenerationMode:
    if value in {
        "baseline",
        "oracle",
        "oracle_karpathy",
        "oracle_dafny",
        "neutral_style",
        "hybrid",
        "modular_discovery",
    }:
        return value
    raise ValueError(f"unknown generation mode in artifact: {value}")


def _oracle_source_for_mode(mode: GenerationMode) -> OracleSource:
    if mode == "oracle_dafny":
        return "dafny"
    if mode == "oracle_karpathy":
        return "karpathy"
    return "zen"


def estimate_token_count(text: str) -> int:
    return (len(text) + 3) // 4


def token_estimate_summary(turns: list[tuple[str, str]]) -> dict[str, Any]:
    prompt_tokens = sum(estimate_token_count(prompt) for prompt, _ in turns)
    completion_tokens = sum(estimate_token_count(completion) for _, completion in turns)
    return {
        "prompt": prompt_tokens,
        "completion": completion_tokens,
        "total": prompt_tokens + completion_tokens,
        "turns": [
            {
                "prompt": estimate_token_count(prompt),
                "completion": estimate_token_count(completion),
                "total": estimate_token_count(prompt) + estimate_token_count(completion),
            }
            for prompt, completion in turns
        ],
    }


def _looks_like_python_source(code: str) -> bool:
    try:
        compile(code, "<candidate>", "exec")
    except SyntaxError:
        return False
    return bool(re.search(r"^\s*(def|class|import|from)\s+", code, re.MULTILINE))


def _looks_like_dafny_source(code: str) -> bool:
    return bool(re.search(r"\b(method|function|predicate|lemma|datatype|class)\b", code))


def _optional_float(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    return float(value)
