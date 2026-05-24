def resolve_flags(defaults: dict[str, bool], segments: dict[str, dict[str, bool]], user: dict) -> dict[str, bool]:
    resolved = dict(defaults)

    for segment_name in user.get("segments", []):
        segment_overrides = segments.get(segment_name)
        if segment_overrides is not None:
            resolved.update(segment_overrides)

    if "overrides" in user:
        resolved.update(user["overrides"])

    return resolved