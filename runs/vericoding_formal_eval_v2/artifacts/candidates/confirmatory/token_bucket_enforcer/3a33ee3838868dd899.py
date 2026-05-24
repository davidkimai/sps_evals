from __future__ import annotations

import time
from typing import Callable, Optional


class TokenBucketEnforcer:
    def __init__(self, capacity: int, refill_rate: float, *, now=None):
        if not isinstance(capacity, int):
            raise TypeError("capacity must be an int")
        if capacity < 0:
            raise ValueError("capacity must be non-negative")
        if not isinstance(refill_rate, (int, float)):
            raise TypeError("refill_rate must be a number")
        if refill_rate < 0:
            raise ValueError("refill_rate must be non-negative")

        self._capacity = capacity
        self._refill_rate = float(refill_rate)
        self._now = now if now is not None else time.monotonic

        if not callable(self._now):
            raise TypeError("now must be callable")

        self._tokens = float(capacity)
        self._last_time = self._now()

    def _refill(self) -> None:
        current = self._now()
        elapsed = current - self._last_time
        self._last_time = current

        if elapsed <= 0:
            return

        self._tokens = min(self._capacity, self._tokens + elapsed * self._refill_rate)

    def allow(self, cost: int = 1) -> bool:
        if not isinstance(cost, int):
            raise TypeError("cost must be an int")
        if cost < 0:
            raise ValueError("cost must be non-negative")

        self._refill()

        if cost > self._tokens:
            return False

        self._tokens -= cost
        if self._tokens > self._capacity:
            self._tokens = float(self._capacity)
        return True