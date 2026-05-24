import time


class TokenBucketEnforcer:
    def __init__(self, capacity: int, refill_rate: float, *, now=None):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self._now = time.monotonic if now is None else now
        self._tokens = float(capacity)
        self._last_refill = float(self._now())

    def _refill(self) -> None:
        current = float(self._now())
        elapsed = current - self._last_refill

        if elapsed > 0:
            self._tokens = min(float(self.capacity), self._tokens + elapsed * self.refill_rate)
            self._last_refill = current
        elif elapsed == 0:
            self._last_refill = current

    def allow(self, cost: int = 1) -> bool:
        self._refill()

        if cost > self._tokens:
            return False

        self._tokens -= cost
        if self._tokens > self.capacity:
            self._tokens = float(self.capacity)

        return True