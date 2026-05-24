from __future__ import annotations

import time


class CircuitBreaker:
    def __init__(self, failure_threshold: int, recovery_timeout: float, *, now=None) -> None:
        if failure_threshold <= 0 or recovery_timeout <= 0:
            raise ValueError('invalid circuit breaker configuration')
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._now = now or time.monotonic
        self.failures = 0
        self.opened_at = None
        self.state = 'closed'

    def call(self, func):
        if self.state == 'open':
            if self._now() - self.opened_at < self.recovery_timeout:
                raise RuntimeError('circuit open')
            self.state = 'half_open'
        try:
            result = func()
        except Exception:
            self.failures += 1
            if self.failures >= self.failure_threshold or self.state == 'half_open':
                self.state = 'open'
                self.opened_at = self._now()
            raise
        self.failures = 0
        self.state = 'closed'
        return result
