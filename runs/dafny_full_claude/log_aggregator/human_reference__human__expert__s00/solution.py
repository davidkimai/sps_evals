from __future__ import annotations


def merge_logs(streams: list) -> list[dict]:
    seen = set()
    merged = []
    for stream in streams:
        for record in stream:
            key = (record.get('source'), record.get('seq'))
            if key in seen:
                continue
            seen.add(key)
            merged.append(dict(record))
    return sorted(merged, key=lambda row: row.get('ts', 0))
