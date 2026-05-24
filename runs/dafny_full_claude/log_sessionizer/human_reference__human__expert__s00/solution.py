def build_sessions(events: list[dict], gap_seconds: int) -> list[dict]:
    valid_events = sorted(_valid_events(events), key=lambda item: (item["user_id"], item["timestamp"]))
    sessions = []
    current = None
    for event in valid_events:
        if current is None or _starts_new_session(current, event, gap_seconds):
            if current is not None:
                sessions.append(current)
            current = {
                "user_id": event["user_id"],
                "start": event["timestamp"],
                "end": event["timestamp"],
                "count": 1,
            }
        else:
            current["end"] = event["timestamp"]
            current["count"] += 1
    if current is not None:
        sessions.append(current)
    return sessions


def _valid_events(events: list[dict]) -> list[dict]:
    return [
        event
        for event in events
        if event.get("user_id") and isinstance(event.get("timestamp"), int)
    ]


def _starts_new_session(current: dict, event: dict, gap_seconds: int) -> bool:
    return current["user_id"] != event["user_id"] or event["timestamp"] - current["end"] > gap_seconds
