from __future__ import annotations

from threading import Lock
from typing import Callable, Generic, TypeVar

T = TypeVar('T')
_MISSING = object()


class LazySingleton(Generic[T]):
    def __init__(self, factory: Callable[[], T]) -> None:
        self._factory = factory
        self._value: T | object = _MISSING
        self._lock = Lock()

    def get(self) -> T:
        if self._value is _MISSING:
            with self._lock:
                if self._value is _MISSING:
                    self._value = self._factory()
        return self._value  # type: ignore[return-value]
