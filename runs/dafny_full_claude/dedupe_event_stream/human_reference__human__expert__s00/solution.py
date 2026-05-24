def dedupe_events(events: list[dict], key_fields: list[str], window_seconds: int) -> list[dict]:
    retained = []
    last_seen: dict[tuple, int] = {}
    for event in events:
        parsed = _parse_event(event, key_fields)
        if parsed is None:
            continue
        timestamp, key = parsed
        previous = last_seen.get(key)
        if previous is not None and timestamp - previous < window_seconds:
            continue
        retained.append(event)
        last_seen[key] = timestamp
    return retained


def _parse_event(event: dict, key_fields: list[str]) -> tuple[int, tuple] | None:
    timestamp = event.get("timestamp")
    if not isinstance(timestamp, int):
        return None
    values = []
    for field in key_fields:
        if field not in event:
            return None
        values.append(event[field])
    return timestamp, tuple(values)
