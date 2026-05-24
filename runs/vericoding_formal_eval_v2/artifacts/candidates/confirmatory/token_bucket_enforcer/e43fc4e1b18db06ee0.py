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

        if now is None:
            self._now: Callable[[], float] = time.monotonic
        else:
            if not callable(now):
                raise TypeError("now must be callable")
            self._now = now

        self._tokens = float(capacity)
        self._last_time = self._current_time()

    def _current_time(self) -> float:
        current = self._now()
        if not isinstance(current, (int, float)):
            raise TypeError("now() must return a number")
        return float(current)

    def _refill(self, current_time: float) -> None:
        elapsed = current_time - self._last_time
        if elapsed <= 0:
            self._last_time = current_time
            return

        added = elapsed * self.refill_rate
        if added > 0:
            self._tokens = min(float(self.capacity), self._tokens + added)

        self._last_time = current_time

    def allow(self, cost: int = 1) -> bool:
        if not isinstance(cost, int):
            raise TypeError("cost must be an int")
        if cost < 0:
            raise ValueError("cost must be non-negative")

        current_time = self._current_time()
        self._refill(current_time)

        if cost > self._tokens:
            return False

        self._tokens -= cost
        if self._tokens > self.capacity:
            self._tokens = float(self.capacity)
        return True