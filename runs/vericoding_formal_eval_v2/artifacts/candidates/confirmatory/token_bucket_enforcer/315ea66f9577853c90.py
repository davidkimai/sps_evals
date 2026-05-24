from __future__ import annotations

import time
from typing import Callable, Optional


class TokenBucketEnforcer:
    def __init__(self, capacity: int, refill_rate: float, *, now=None):
        if capacity < 0:
            raise ValueError("capacity must be non-negative")
        if refill_rate < 0:
            raise ValueError("refill_rate must be non-negative")

        self.capacity = int(capacity)
        self.refill_rate = float(refill_rate)
        self._now = now if now is not None else time.monotonic

        current = self._now()
        self._tokens = float(self.capacity)
        self._last_time = float(current)

    def _refill(self) -> None:
        current = float(self._now())
        elapsed = current - self._last_time
        if elapsed > 0:
            self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)
            self._last_time = current
        else:
            self._last_time = current

    def allow(self, cost: int = 1) -> bool:
        if cost < 0:
            raise ValueError("cost must be non-negative")

        self._refill()

        if cost <= self._tokens:
            self._tokens -= cost
            return True
        return False