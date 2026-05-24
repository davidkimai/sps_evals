from copy import deepcopy


def merge_settings(defaults: dict, file_config: dict, env: dict[str, str]) -> dict:
    merged = _deep_merge(defaults, file_config)
    for key, value in env.items():
        if key.startswith("APP__"):
            path = [part.lower() for part in key[5:].split("__") if part]
            if path:
                _assign_path(merged, path, _parse_env_value(value))
    return merged


def _deep_merge(left: dict, right: dict) -> dict:
    result = deepcopy(left)
    for key, value in right.items():
        if isinstance(result.get(key), dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def _assign_path(target: dict, path: list[str], value):
    current = target
    for segment in path[:-1]:
        existing = current.get(segment)
        if not isinstance(existing, dict):
            existing = {}
            current[segment] = existing
        current = existing
    current[path[-1]] = value


def _parse_env_value(value: str):
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
        return int(value)
    if "," in value:
        return [part.strip() for part in value.split(",") if part.strip()]
    return value
