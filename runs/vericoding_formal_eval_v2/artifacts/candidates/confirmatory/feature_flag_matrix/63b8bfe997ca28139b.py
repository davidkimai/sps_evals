def resolve_flags(
    defaults: dict[str, bool],
    segments: dict[str, dict[str, bool]],
    user: dict,
) -> dict[str, bool]:
    resolved: dict[str, bool] = {}

    for flag_name, flag_value in defaults.items():
        resolved[flag_name] = flag_value

    user_segments = user.get("segments", [])
    for segment_name in user_segments:
        if segment_name not in segments:
            continue

        segment_overrides = segments[segment_name]
        for flag_name, flag_value in segment_overrides.items():
            resolved[flag_name] = flag_value

    if "overrides" in user:
        user_overrides = user["overrides"]
        for flag_name, flag_value in user_overrides.items():
            resolved[flag_name] = flag_value

    return resolved