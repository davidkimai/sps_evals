from __future__ import annotations

from copy import deepcopy
from typing import Any


def resolve_flags(defaults: dict[str, bool], segments: dict[str, dict[str, bool]], user: dict) -> dict[str, bool]:
    result: dict[str, bool] = dict(defaults)

    user_segments = user.get("segments", [])
    if user_segments is None:
        user_segments = []

    for segment_name in user_segments:
        if segment_name in segments:
            for flag_name, flag_value in segments[segment_name].items():
                result[flag_name] = bool(flag_value)

    overrides = user.get("overrides")
    if overrides is not None:
        for flag_name, flag_value in overrides.items():
            result[flag_name] = bool(flag_value)

    return result


def explain_flags(defaults: dict[str, bool], segments: dict[str, dict[str, bool]], user: dict) -> dict[str, dict]:
    final_flags = resolve_flags(defaults, segments, user)
    explanation: dict[str, dict[str, Any]] = {}

    sources: dict[str, str] = {flag_name: "default" for flag_name in defaults}

    user_segments = user.get("segments", [])
    if user_segments is None:
        user_segments = []

    for segment_name in user_segments:
        if segment_name in segments:
            for flag_name in segments[segment_name]:
                sources[flag_name] = f"segment:{segment_name}"

    overrides = user.get("overrides")
    if overrides is not None:
        for flag_name in overrides:
            sources[flag_name] = "user_override"

    for flag_name, flag_value in final_flags.items():
        explanation[flag_name] = {
            "value": flag_value,
            "source": sources.get(flag_name, "default"),
        }

    return explanation