from typing import Any


def _copy_mapping_values(source: dict[str, bool]) -> dict[str, bool]:
    return dict(source)


def _segment_names_for_user(user: dict[str, Any]) -> list[str]:
    names = user.get("segments", [])
    if names is None:
        return []
    return list(names)


def _apply_updates(target: dict[str, bool], updates: dict[str, bool]) -> None:
    for key, value in updates.items():
        target[key] = value


def resolve_flags(
    defaults: dict[str, bool],
    segments: dict[str, dict[str, bool]],
    user: dict,
) -> dict[str, bool]:
    resolved = _copy_mapping_values(defaults)

    for segment_name in _segment_names_for_user(user):
        segment_overrides = segments.get(segment_name)
        if segment_overrides is not None:
            _apply_updates(resolved, segment_overrides)

    if "overrides" in user:
        _apply_updates(resolved, user["overrides"])

    return resolved