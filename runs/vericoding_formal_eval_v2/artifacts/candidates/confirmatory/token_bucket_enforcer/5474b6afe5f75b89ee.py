import time
from typing import Callable, Optional


class TokenBucketEnforcer:
    def __init__(self, capacity: int, refill_rate: float, *, now: Optional[Callable[[], float]] = None):
        if not isinstance(capacity, int):
            raise TypeError("capacity must be an int")
        if capacity < 0:
            raise ValueError("capacity must be non-negative")
        if not isinstance(refill_rate, (int, float)):
            raise TypeError("refill_rate must be a number")
        if refill_rate < 0:
            raise ValueError("refill_rate must be non-negative")
        if now is not None and not callable(now):
            raise TypeError("now must be callable")

        self.capacity = capacity
        self.refill_rate = float(refill_rate)
        self._now = now if now is not None else time.monotonic
        self._tokens = float(capacity)
        self._last_refill = float(self._now())

    def _refill(self) -> None:
        current = float(self._now())
        elapsed = current - self._last_refill

        if elapsed <= 0:
            return

        if self.refill_rate > 0 and self._tokens < self.capacity:
            self._tokens = min(
                float(self.capacity),
                self._tokens + elapsed * self.refill_rate,
            )

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