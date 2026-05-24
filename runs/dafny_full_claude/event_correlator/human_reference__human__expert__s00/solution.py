from __future__ import annotations


def correlate_events(events: list[dict], *, within: int) -> list[tuple[dict, dict]]:
    ordered = sorted(events, key=lambda row: row.get('ts', 0))
    pairs = []
    for left in ordered:
        if left.get('type') != 'A':
            continue
        for right in ordered:
            if right.get('session_id') != left.get('session_id') or right.get('type') != 'B':
                continue
            if 0 < right.get('ts', 0) - left.get('ts', 0) <= within:
                pairs.append((left, right))
                break
    return pairs
