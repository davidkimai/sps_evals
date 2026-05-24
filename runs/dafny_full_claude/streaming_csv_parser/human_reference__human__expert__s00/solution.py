from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator


def parse_csv_rows(lines: Iterable[str]) -> Iterator[dict[str, str]]:
    iterator = iter(lines)
    header: list[str] | None = None
    for raw in iterator:
        line = raw.strip()
        if not line:
            continue
        header = [cell.strip() for cell in line.split(',')]
        break
    if header is None:
        return
    for raw in iterator:
        line = raw.strip()
        if not line:
            continue
        cells = [cell.strip() for cell in line.split(',')]
        yield dict(zip(header, cells))
