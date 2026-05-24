from __future__ import annotations

import hmac
from typing import Union


def timing_safe_compare(left: Union[str, bytes], right: Union[str, bytes]) -> bool:
    """
    Compare two values in a timing-safe manner.

    Visible invariants and precedence rules:
    - Only str and bytes are accepted.
    - Both inputs must have the same type.
    - If either input is not str or bytes, raise TypeError.
    - If the types differ, raise TypeError.
    - Otherwise, return the result of hmac.compare_digest(left, right).
    """
    left_type = type(left)
    right_type = type(right)

    allowed_types = (str, bytes)

    if left_type not in allowed_types or right_type not in allowed_types:
        raise TypeError("timing_safe_compare accepts only str or bytes inputs")

    if left_type is not right_type:
        raise TypeError("timing_safe_compare requires both inputs to have the same type")

    return hmac.compare_digest(left, right)