from __future__ import annotations

import weakref
from typing import Any


class ObjectRegistry:
    def __init__(self) -> None:
        self._refs: dict[str, weakref.ReferenceType[Any]] = {}

    def register(self, key: str, obj: object) -> None:
        self._refs[key] = weakref.ref(obj)

    def get(self, key: str):
        ref = self._refs.get(key)
        return None if ref is None else ref()

    def cleanup(self) -> None:
        self._refs = {key: ref for key, ref in self._refs.items() if ref() is not None}
