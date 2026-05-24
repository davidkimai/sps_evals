from __future__ import annotations

from copy import deepcopy
from typing import Any


def resolve_flags(defaults: dict[str, bool], segments: dict[str, dict[str, bool]], user: dict) -> dict[str, bool]:
    """
    Resolve feature flags from defaults, segment overrides, and user overrides.

    Rules:
    - Start from defaults.
    - If user contains "segments" as a list, apply matching segment overrides
      in the listed order, ignoring unknown segments.
    - Then apply user["overrides"] if present.
    - Return a new dictionary and do not mutate inputs.
    """
    result: dict[str, bool] = dict(defaults)

    user_segments = user.get("segments")
    if isinstance(user_segments, list):
        for segment_name in user_segments:
            if segment_name in segments:
                segment_overrides = segments[segment_name]
                if isinstance(segment_overrides, dict):
                    result.update(segment_overrides)

    if "overrides" in user:
        overrides = user["overrides"]
        if isinstance(overrides, dict):
            result.update(overrides)

    return result