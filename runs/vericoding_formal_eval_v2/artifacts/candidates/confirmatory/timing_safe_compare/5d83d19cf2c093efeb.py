from __future__ import annotations

from typing import Optional, Union


def timing_safe_compare(
    left,
    right,
    pad_to_length: int | None = None,
    pad_char: str = "\0",
) -> bool:
    """
    Timing-safe comparison for same-typed strings or bytes.

    Rules:
    - Accept only str or bytes.
    - Both inputs must have the same type; otherwise raise TypeError.
    - If pad_to_length is provided for strings, right-pad both strings to that length
      using pad_char before comparing.
    - pad_char must be exactly one character when used with strings.
    - For bytes, padding is not supported; pad_to_length must be None.
    - Comparison is performed using hmac.compare_digest where possible.
    """
    import hmac

    if not isinstance(left, (str, bytes)) or not isinstance(right, (str, bytes)):
        raise TypeError("timing_safe_compare accepts only str or bytes")

    if type(left) is not type(right):
        raise TypeError("left and right must have the same type")

    if isinstance(left, str):
        if pad_to_length is not None:
            if not isinstance(pad_to_length, int):
                raise TypeError("pad_to_length must be an int or None")
            if pad_to_length < 0:
                raise ValueError("pad_to_length must be non-negative")
            if not isinstance(pad_char, str):
                raise TypeError("pad_char must be a str")
            if len(pad_char) != 1:
                raise ValueError("pad_char must be exactly one character")
            left = left.ljust(pad_to_length, pad_char)
            right = right.ljust(pad_to_length, pad_char)
        return hmac.compare_digest(left, right)

    # bytes
    if pad_to_length is not None:
        raise TypeError("pad_to_length is only supported for str inputs")
    return hmac.compare_digest(left, right)