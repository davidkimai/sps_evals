def resolve_flags(defaults: dict[str, bool], segments: dict[str, dict[str, bool]], user: dict) -> dict[str, bool]:
    """
    Visible invariants and precedence:
    1. The returned mapping is a new dictionary.
    2. Inputs are not mutated.
    3. Defaults provide the initial flag values.
    4. Segment overrides are applied in the exact order listed by user["segments"].
    5. Unknown segment names are ignored.
    6. User overrides, when present, have final precedence.
    """
    resolved = dict(defaults)

    user_segments = user.get("segments", [])
    for segment_name in user_segments:
        segment_overrides = segments.get(segment_name)
        if segment_overrides is not None:
            resolved.update(segment_overrides)

    if "overrides" in user:
        resolved.update(user["overrides"])

    return resolved