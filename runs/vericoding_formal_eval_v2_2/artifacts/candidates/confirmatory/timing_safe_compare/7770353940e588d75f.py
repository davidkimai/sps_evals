"""Timing-safe comparison helper."""

from __future__ import annotations

import hmac


def timing_safe_compare(left: str | bytes, right: str | bytes) -> bool:
    """Compare two str or bytes values using hmac.compare_digest.

    Both inputs must be exactly the same supported type: str with str, or bytes
    with bytes. Unsupported types or mixed supported types raise TypeError.
    """
    left_type = type(left)
    right_type = type(right)

    if left_type is not right_type:
        raise TypeError("timing_safe_compare arguments must have the same type")

    if left_type is str:
        return bool(hmac.compare_digest(left, right))

    if left_type is bytes:
        return bool(hmac.compare_digest(left, right))

    raise TypeError("timing_safe_compare arguments must be str or bytes")


__all__ = ["timing_safe_compare"]