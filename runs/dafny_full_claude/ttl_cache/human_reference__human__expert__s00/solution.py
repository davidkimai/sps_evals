from __future__ import annotations

import time
from collections import OrderedDict
from collections.abc import Callable
from typing import Any


class TTLCache:
    def __init__(self, max_size: int, ttl_seconds: float, *, now: Callable[[], float] | None = None) -> None:
        if max_size <= 0 or ttl_seconds <= 0:
            raise ValueError('max_size and ttl_seconds must be positive')
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._now = now or time.monotonic
        self._items: OrderedDict[Any, tuple[Any, float]] = OrderedDict()

    def set(self, key, value) -> None:
        self._items[key] = (value, self._now())
        self._items.move_to_end(key)
        while len(self._items) > self._max_size:
            self._items.popitem(last=False)

    def get(self, key):
        item = self._items.get(key)
        if item is None:
            return None
        value, stamp = item
        if self._now() - stamp > self._ttl:
            del self._items[key]
            return None
        self._items.move_to_end(key)
        return value
