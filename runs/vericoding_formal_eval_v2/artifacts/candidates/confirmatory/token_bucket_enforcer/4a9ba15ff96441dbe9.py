import time
from typing import Optional, Callable


class TokenBucketEnforcer:
    def __init__(self, capacity: int, refill_rate: float, *, now=None):
        if capacity < 0:
            raise ValueError("capacity must be non-negative")
        if refill_rate < 0:
            raise ValueError("refill_rate must be non-negative")

        self.capacity = int(capacity)
        self.refill_rate = float(refill_rate)
        self._now = now if now is not None else time.monotonic

        current_time = self._now()
        self._tokens = float(self.capacity)
        self._last_refill_time = float(current_time)

    def _refill(self) -> None:
        current_time = float(self._now())
        elapsed = current_time - self._last_refill_time
        if elapsed <= 0:
            return

        if self.refill_rate > 0 and self.capacity > 0:
            self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)
        else:
            self._tokens = min(self.capacity, self._tokens)

        self._last_refill_time = current_time

    def allow(self, cost: int = 1) -> bool:
        if cost < 0:
            raise ValueError("cost must be non-negative")

        self._refill()

        if cost > self._tokens:
            return False

        self._tokens -= cost
        if self._tokens < 0:
            self._tokens = 0.0
        return True