import time
from typing import Callable, Optional


class TokenBucketEnforcer:
    def __init__(self, capacity: int, refill_rate: float, *, now: Optional[Callable[[], float]] = None):
        if not isinstance(capacity, int):
            raise TypeError("capacity must be an int")
        if capacity < 0:
            raise ValueError("capacity must be non-negative")

        refill_rate = float(refill_rate)
        if refill_rate < 0:
            raise ValueError("refill_rate must be non-negative")

        if now is None:
            now = time.monotonic
        if not callable(now):
            raise TypeError("now must be callable")

        self.capacity = capacity
        self.refill_rate = refill_rate
        self._now = now
        self._tokens = float(capacity)
        self._last_refill = float(self._now())

    def _refill(self) -> None:
        current = float(self._now())
        elapsed = current - self._last_refill

        if elapsed <= 0:
            return

        added = elapsed * self.refill_rate
        self._tokens = min(float(self.capacity), self._tokens + added)
        self._last_refill = current

    def allow(self, cost: int = 1) -> bool:
        if not isinstance(cost, int):
            raise TypeError("cost must be an int")
        if cost < 0:
            raise ValueError("cost must be non-negative")

        self._refill()

        if float(cost) > self._tokens:
            return False

        self._tokens -= float(cost)
        return True