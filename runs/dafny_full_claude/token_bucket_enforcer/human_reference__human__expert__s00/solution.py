from __future__ import annotations

import time
from collections.abc import Callable


class TokenBucketEnforcer:
    def __init__(self, capacity: int, refill_rate: float, *, now: Callable[[], float] | None = None) -> None:
        if capacity <= 0 or refill_rate <= 0:
            raise ValueError('capacity and refill_rate must be positive')
        self._capacity = capacity
        self._refill_rate = refill_rate
        self._now = now or time.monotonic
        self._tokens = float(capacity)
        self._last = self._now()

    def allow(self, cost: int = 1) -> bool:
        if cost <= 0:
            raise ValueError('cost must be positive')
        current = self._now()
        elapsed = max(0.0, current - self._last)
        self._tokens = min(float(self._capacity), self._tokens + elapsed * self._refill_rate)
        self._last = current
        if self._tokens < cost:
            return False
        self._tokens -= cost
        return True
