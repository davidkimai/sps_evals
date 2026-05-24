from __future__ import annotations

from typing import Any


def _copy_defaults(defaults: dict[str, bool]) -> dict[str, bool]:
    return dict(defaults)


def _apply_segment_overrides(
    result: dict[str, bool],
    segments: dict[str, dict[str, bool]],
    selected_segments: Any,
) -> None:
    if not isinstance(selected_segments, list):
        return

    for segment_name in selected_segments:
        if not isinstance(segment_name, str):
            continue
        segment_overrides = segments.get(segment_name)
        if not segment_overrides:
            continue
        for flag_name, flag_value in segment_overrides.items():
            result[flag_name] = flag_value


def _apply_user_overrides(result: dict[str, bool], user: dict) -> None:
    overrides = user.get("overrides")
    if not isinstance(overrides, dict):
        return
    for flag_name, flag_value in overrides.items():
        result[flag_name] = flag_value


def resolve_flags(
    defaults: dict[str, bool],
    segments: dict[str, dict[str, bool]],
    user: dict,
) -> dict[str, bool]:
    result = _copy_defaults(defaults)
    _apply_segment_overrides(result, segments, user.get("segments"))
    _apply_user_overrides(result, user)
    return result