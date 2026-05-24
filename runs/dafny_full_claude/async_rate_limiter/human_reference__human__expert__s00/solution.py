from __future__ import annotations

import time
from collections import deque
from typing import Callable


class AsyncRateLimiter:
    def __init__(self, rate: int, *, now: Callable[[], float] | None = None) -> None:
        if rate <= 0:
            raise ValueError('rate must be positive')
        self._rate = rate
        self._now = now or time.monotonic
        self._hits: deque[float] = deque()

    async def acquire(self) -> bool:
        current = self._now()
        while self._hits and current - self._hits[0] >= 1.0:
            self._hits.popleft()
        if len(self._hits) >= self._rate:
            return False
        self._hits.append(current)
        return True
