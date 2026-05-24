from __future__ import annotations

from typing import Any


def resolve_flags(defaults: dict[str, bool], segments: dict[str, dict[str, bool]], user: dict) -> dict[str, bool]:
    result: dict[str, bool] = dict(defaults)

    user_segments = user.get("segments")
    if isinstance(user_segments, list):
        for segment_name in user_segments:
            if segment_name in segments:
                segment_overrides = segments[segment_name]
                for key, value in segment_overrides.items():
                    result[key] = value

    user_overrides = user.get("overrides")
    if isinstance(user_overrides, dict):
        for key, value in user_overrides.items():
            result[key] = value

    return result