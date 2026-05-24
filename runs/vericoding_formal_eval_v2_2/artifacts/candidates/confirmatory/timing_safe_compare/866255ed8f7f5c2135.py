import hmac
from typing import Union

Comparable = Union[str, bytes]

__all__ = ["timing_safe_compare"]


def _require_supported_pair(left: object, right: object) -> None:
    left_type = type(left)
    right_type = type(right)

    if left_type is not right_type:
        raise TypeError("left and right must have the same type")

    if left_type is not str and left_type is not bytes:
        raise TypeError("left and right must be str or bytes")


def timing_safe_compare(left: Comparable, right: Comparable) -> bool:
    _require_supported_pair(left, right)
    return bool(hmac.compare_digest(left, right))