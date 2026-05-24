from __future__ import annotations

from typing import Dict, List, Any


def resolve_flags(
    defaults: dict[str, bool],
    segments: dict[str, dict[str, bool]],
    user: dict,
) -> dict[str, bool]:
    """
    Resolve feature flags using the following precedence:

    1. Start with a copy of defaults.
    2. If user contains "segments" as a list, apply each named segment override
       in the listed order.
       - Unknown segment names are ignored.
       - Segment overrides are applied by updating the current flag state with
         that segment's mapping.
    3. If user contains "overrides", apply those last.
    4. Return a new dictionary without mutating any input.

    Visible contract only guarantees bool values in the provided mappings.
    """
    resolved: dict[str, bool] = dict(defaults)

    user_segments = user.get("segments")
    if isinstance(user_segments, list):
        for segment_name in user_segments:
            if segment_name in segments:
                segment_overrides = segments[segment_name]
                resolved.update(segment_overrides)

    user_overrides = user.get("overrides")
    if isinstance(user_overrides, dict):
        resolved.update(user_overrides)

    return resolved