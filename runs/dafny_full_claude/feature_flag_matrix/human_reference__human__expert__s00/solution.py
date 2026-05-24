def resolve_flags(defaults: dict[str, bool], segments: dict[str, dict[str, bool]], user: dict) -> dict[str, bool]:
    resolved = dict(defaults)
    for segment_name in user.get("segments", []):
        resolved.update(segments.get(segment_name, {}))
    resolved.update(user.get("overrides", {}))
    return resolved
