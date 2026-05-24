import time
import math
from typing import Callable, Optional


class TokenBucketEnforcer:
    # Visible invariants and precedence rules:
    # 1. The token balance is always clamped to the inclusive range [0, capacity].
    # 2. Refill is applied before each allow/deny decision.
    # 3. Refill amount is elapsed_time * refill_rate, capped by capacity.
    # 4. A request is denied when cost exceeds the currently available tokens.
    # 5. Denied requests do not consume tokens.
    # 6. Allowed requests consume exactly cost tokens.
    # 7. Backward clock movement does not create tokens.

    def __init__(
        self,
        capacity: int,
        refill_rate: float,
        *,
        now: Optional[Callable[[], float]] = None,
    ):
        if not isinstance(capacity, int):
            raise TypeError("capacity must be an int")
        if capacity < 0:
            raise ValueError("capacity must be non-negative")

        if not isinstance(refill_rate, (int, float)):
            raise TypeError("refill_rate must be a float")
        refill_rate = float(refill_rate)
        if not math.isfinite(refill_rate):
            raise ValueError("refill_rate must be finite")
        if refill_rate < 0:
            raise ValueError("refill_rate must be non-negative")

        if now is None:
            self._now = time.monotonic
        elif callable(now):
            self._now = now
        else:
            raise TypeError("now must be callable or None")

        self.capacity = capacity
        self.refill_rate = refill_rate
        self._tokens = float(capacity)
        self._last_refill = float(self._now())

    def _refill(self) -> None:
        current_time = float(self._now())

        if current_time <= self._last_refill:
            return

        elapsed = current_time - self._last_refill
        self._last_refill = current_time

        if self.capacity == 0 or self.refill_rate == 0:
            return

        added_tokens = elapsed * self.refill_rate
        if added_tokens <= 0:
            return

        self._tokens = min(float(self.capacity), self._tokens + added_tokens)

    def allow(self, cost: int = 1) -> bool:
        if not isinstance(cost, int):
            raise TypeError("cost must be an int")
        if cost < 0:
            raise ValueError("cost must be non-negative")

        self._refill()

        if float(cost) > self._tokens:
            return False

        self._tokens -= float(cost)
        if self._tokens < 0:
            self._tokens = 0.0
        elif self._tokens > self.capacity:
            self._tokens = float(self.capacity)

        return True