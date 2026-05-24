def resolve_flags(defaults: dict[str, bool], segments: dict[str, dict[str, bool]], user: dict) -> dict[str, bool]:
    resolved = dict(defaults)

    for segment_name in user.get("segments", []):
        if segment_name in segments:
            resolved.update(segments[segment_name])

    if "overrides" in user:
        resolved.update(user["overrides"])

    return resolved