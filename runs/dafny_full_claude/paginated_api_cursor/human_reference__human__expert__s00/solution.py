from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any


async def collect_cursor_items(
    fetch_page: Callable[[Any], Awaitable[tuple[list[Any], Any]]],
    *,
    start_cursor: Any = None,
) -> list[Any]:
    cursor = start_cursor
    collected: list[Any] = []
    while True:
        items, cursor = await fetch_page(cursor)
        collected.extend(items)
        if cursor is None:
            return collected
