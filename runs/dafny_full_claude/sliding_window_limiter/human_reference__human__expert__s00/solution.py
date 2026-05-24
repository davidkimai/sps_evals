class SlidingWindowLimiter:
    def __init__(self, limit: int, window_seconds: int):
        if limit <= 0 or window_seconds <= 0:
            raise ValueError("limit and window_seconds must be positive")
        self._limit = limit
        self._window_seconds = window_seconds
        self._events: dict[str, list[int]] = {}

    def allow(self, key: str, timestamp: int) -> bool:
        retained = self._retained_events(key, timestamp)
        if len(retained) >= self._limit:
            return False
        retained.append(timestamp)
        self._events[key] = retained
        return True

    def snapshot(self, key: str) -> list[int]:
        return list(self._events.get(key, []))

    def _retained_events(self, key: str, timestamp: int) -> list[int]:
        floor = timestamp - self._window_seconds
        retained = [item for item in self._events.get(key, []) if item > floor]
        self._events[key] = retained
        return retained
