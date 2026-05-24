from __future__ import annotations

import hmac
from typing import Union

_StrOrBytes = Union[str, bytes]


def timing_safe_compare(left: _StrOrBytes, right: _StrOrBytes) -> bool:
    """
    Compare two values in a timing-safe manner.

    Accepts only str or bytes. Both inputs must have the same type;
    otherwise TypeError is raised.
    """
    if not isinstance(left, (str, bytes)) or not isinstance(right, (str, bytes)):
        raise TypeError("timing_safe_compare accepts only str or bytes")

    if type(left) is not type(right):
        raise TypeError("timing_safe_compare requires both inputs to have the same type")

    return hmac.compare_digest(left, right)