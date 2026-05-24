from __future__ import annotations

import hmac
from typing import Union


def _validate_operand(value: object, name: str) -> Union[str, bytes]:
    if isinstance(value, (str, bytes)):
        return value
    raise TypeError(f"{name} must be str or bytes")


def timing_safe_compare(left, right) -> bool:
    left_value = _validate_operand(left, "left")
    right_value = _validate_operand(right, "right")

    if type(left_value) is not type(right_value):
        raise TypeError("left and right must have the same type")

    return hmac.compare_digest(left_value, right_value)