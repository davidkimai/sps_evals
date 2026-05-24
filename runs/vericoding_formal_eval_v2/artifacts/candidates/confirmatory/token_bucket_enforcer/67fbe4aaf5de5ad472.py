import time
from numbers import Real


class TokenBucketEnforcer:
    def __init__(self, capacity: int, refill_rate: float, *, now=None):
        if isinstance(capacity, bool) or not isinstance(capacity, int):
            raise TypeError("capacity must be an int")
        if capacity < 0:
            raise ValueError("capacity must be non-negative")
        if isinstance(refill_rate, bool) or not isinstance(refill_rate, Real):
            raise TypeError("refill_rate must be a number")
        if refill_rate < 0:
            raise ValueError("refill_rate must be non-negative")
        if now is None:
            clock = time.monotonic
        else:
            if not callable(now):
                raise TypeError("now must be callable")
            clock = now

        initial_time = clock()
        if isinstance(initial_time, bool) or not isinstance(initial_time, Real):
            raise TypeError("now() must return a number")

        self.capacity = capacity
        self.refill_rate = float(refill_rate)
        self._now = clock
        self._tokens = float(capacity)
        self._last_refill = float(initial_time)

    def allow(self, cost: int = 1) -> bool:
        if isinstance(cost, bool) or not isinstance(cost, int):
            raise TypeError("cost must be an int")
        if cost < 0:
            raise ValueError("cost must be non-negative")

        self._refill()

        requested = float(cost)
        if requested > self._tokens:
            return False

        self._tokens -= requested
        return True

    def _refill(self) -> None:
        current_time = self._now()
        if isinstance(current_time, bool) or not isinstance(current_time, Real):
            raise TypeError("now() must return a number")

        current = float(current_time)
        previous = self._last_refill

        if current <= previous:
            return

        elapsed = current - previous
        added = elapsed * self.refill_rate
        updated = self._tokens + added

        if updated > float(self.capacity):
            self._tokens = float(self.capacity)
        else:
            self._tokens = updated

        self._last_refill = current

    @property
    def tokens(self) -> float:
        self._refill()
        return self._tokens