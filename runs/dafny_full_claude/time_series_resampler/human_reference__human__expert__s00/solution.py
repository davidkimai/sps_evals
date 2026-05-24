from __future__ import annotations


def resample_series(points: list[tuple[int, float]], *, start: int, end: int, interval: int) -> list[tuple[int, float | None]]:
    ordered = sorted(points)
    index = 0
    current = None
    output = []
    for timestamp in range(start, end + 1, interval):
        while index < len(ordered) and ordered[index][0] <= timestamp:
            current = ordered[index][1]
            index += 1
        output.append((timestamp, current))
    return output
