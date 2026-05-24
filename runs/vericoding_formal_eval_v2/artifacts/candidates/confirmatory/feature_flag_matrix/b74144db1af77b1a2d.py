from typing import Any


def _resolve_with_sources(
    defaults: dict[str, bool],
    segments: dict[str, dict[str, bool]],
    user: dict,
) -> tuple[dict[str, bool], dict[str, str]]:
    resolved: dict[str, bool] = {}
    sources: dict[str, str] = {}

    for flag, value in defaults.items():
        resolved[flag] = value
        sources[flag] = "default"

    user_segments = user.get("segments", ())
    if user_segments is None:
        user_segments = ()

    for segment_name in user_segments:
        if segment_name not in segments:
            continue

        segment_overrides = segments[segment_name]
        for flag, value in segment_overrides.items():
            resolved[flag] = value
            sources[flag] = f"segment:{segment_name}"

    user_overrides = user.get("overrides")
    if user_overrides is not None:
        for flag, value in user_overrides.items():
            resolved[flag] = value
            sources[flag] = "user_override"

    return resolved, sources


def resolve_flags(
    defaults: dict[str, bool],
    segments: dict[str, dict[str, bool]],
    user: dict,
) -> dict[str, bool]:
    resolved, _ = _resolve_with_sources(defaults, segments, user)
    return resolved


def explain_flags(defaults, segments, user) -> dict[str, dict]:
    resolved, sources = _resolve_with_sources(defaults, segments, user)
    return {
        flag: {
            "value": value,
            "source": sources[flag