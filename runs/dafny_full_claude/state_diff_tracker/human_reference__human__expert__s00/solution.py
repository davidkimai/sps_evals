from __future__ import annotations


def diff_versions(previous: dict, current: dict) -> list[dict]:
    changes = []
    for field in sorted(set(previous) | set(current)):
        before = previous.get(field)
        after = current.get(field)
        if before != after:
            changes.append({'field': field, 'before': before, 'after': after})
    return changes
