_MISSING = object()


def extract_fields(record: dict, paths: dict[str, str], default=None) -> dict:
    result = {}
    for output_key, path in paths.items():
        value = _resolve_path(record, path)
        result[output_key] = default if value is _MISSING else value
    return result


def _resolve_path(value, path: str):
    current = value
    for segment in path.split("."):
        if isinstance(current, dict):
            if segment not in current:
                return _MISSING
            current = current[segment]
        elif isinstance(current, list) and segment.isdigit():
            index = int(segment)
            if index >= len(current):
                return _MISSING
            current = current[index]
        else:
            return _MISSING
    return current
