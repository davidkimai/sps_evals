from __future__ import annotations

import time
from typing import Callable, Optional


class TokenBucketEnforcer:
    def __init__(self, capacity: int, refill_rate: float, *, burst: int = 0, now=None):
        if not isinstance(capacity, int):
            raise TypeError("capacity must be an int")
        if not isinstance(burst, int):
            raise TypeError("burst must be an int")
        if capacity < 0:
            raise ValueError("capacity must be non-negative")
        if burst < 0:
            raise ValueError("burst must be non-negative")
        if refill_rate < 0:
            raise ValueError("refill_rate must be non-negative")

        self.capacity = capacity
        self.burst = burst
        self.refill_rate = float(refill_rate)
        self._max_tokens = capacity + burst

        if now is None:
            self._now: Callable[[], float] = time.monotonic
        else:
            if not callable(now):
                raise TypeError("now must be callable or None")
            self._now = now

        self._tokens = float(self._max_tokens)
        self._last_time: Optional[float] = self._now()

    def _refill(self) -> None:
        current = self._now()
        if self._last_time is None:
            self._last_time = current
            return

        elapsed = current - self._last_time
        if elapsed > 0 and self.refill_rate > 0:
            self._tokens = min(self._max_tokens, self._tokens + elapsed * self.refill_rate)
        self._last_time = current

    def allow(self, cost: int = 1) -> bool:
        if not isinstance(cost, int):
            raise TypeError("cost must be an int")
        if cost < 0:
            raise ValueError("cost must be non-negative")

        self._refill()

        if cost <= self._tokens:
            self._tokens -= cost
            return True
        return False