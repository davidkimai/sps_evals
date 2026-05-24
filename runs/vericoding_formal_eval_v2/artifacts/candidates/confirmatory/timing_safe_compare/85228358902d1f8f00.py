"""Timing-safe equality helper.

Visible invariants and precedence rules:
1. Only exact ``str`` or exact ``bytes`` inputs are accepted.
2. The two inputs must have the same exact type.
3. Type validation happens before calling ``hmac.compare_digest``.
4. The result is the boolean result of ``hmac.compare_digest``.
"""

from __future__ import annotations

import hmac
from typing import overload


_ALLOWED_TYPES = (str, bytes)


@overload
def timing_safe_compare(left: str, right: str) -> bool:
    ...


@overload
def timing_safe_compare(left: bytes, right: bytes) -> bool:
    ...


def timing_safe_compare(left: object, right: object) -> bool:
    """Compare two same-typed strings or byte strings using hmac.compare_digest."""
    left_type = type(left)
    right_type = type(right)

    if left_type not in _ALLOWED_TYPES:
        raise TypeError("left must be str or bytes")
    if right_type not in _ALLOWED_TYPES:
        raise TypeError("right must be str or bytes")
    if left_type is not right_type:
        raise TypeError("left and right must have the same type")

    return hmac.compare_digest(left, right)


__all__ = ["timing_safe_compare"]