from __future__ import annotations

import hmac
from typing import Union


def timing_safe_compare(left: Union[str, bytes], right: Union[str, bytes]) -> bool:
    """
    Compare two values in a timing-safe manner.

    Accepts only str or bytes. Both inputs must have the same type.
    Raises TypeError for unsupported types or mixed types.
    """
    left_is_str = isinstance(left, str)
    left_is_bytes = isinstance(left, bytes)
    right_is_str = isinstance(right, str)
    right_is_bytes = isinstance(right, bytes)

    if not ((left_is_str or left_is_bytes) and (right_is_str or right_is_bytes)):
        raise TypeError("timing_safe_compare accepts only str or bytes")

    if type(left) is not type(right):
        raise TypeError("timing_safe_compare requires both inputs to have the same type")

    return hmac.compare_digest(left, right)