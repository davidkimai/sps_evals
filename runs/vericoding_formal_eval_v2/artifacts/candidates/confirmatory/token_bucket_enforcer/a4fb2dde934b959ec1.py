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

        self.capacity = capacity
        self.refill_rate = float(refill_rate)
        self._now = now if now is not None else time.monotonic

        if not callable(self._now):
            raise TypeError("now must be callable or None")

        self._tokens = float(capacity)
        self._last_time = self._current_time()

    def _current_time(self) -> float:
        value = self._now()
        if not isinstance(value, (int, float)):
            raise TypeError("now() must return a number")
        return float(value)

    def _refill(self) -> None:
        current = self._current_time()
        elapsed = current - self._last_time
        self._last_time = current

        if elapsed <= 0:
            return

        self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)

    def allow(self, cost: int = 1) -> bool:
        if not isinstance(cost, int):
            raise TypeError("cost must be an int")
        if cost < 0:
            raise ValueError("cost must be non-negative")

        self._refill()

        if cost > self._tokens:
            return False

        self._tokens -= cost
        if self._tokens > self.capacity:
            self._tokens = float(self.capacity)
        return True