from __future__ import annotations

import hmac
from typing import Union

__all__ = ["timing_safe_compare"]


def timing_safe_compare(left: Union[str, bytes], right: Union[str, bytes]) -> bool:
    """
    Compare two str or bytes values using hmac.compare_digest.

    Both inputs must be str or bytes and must have the same type.
    """
    if not isinstance(left, (str, bytes)):
        raise TypeError("left must be str or bytes")
    if not isinstance(right, (str, bytes)):
        raise TypeError("right must be str or bytes")
    if type(left) is not type(right):
        raise TypeError("left and right must have the same type")

    return hmac.compare_digest(left, right)