import hmac
from typing import overload


@overload
def timing_safe_compare(left: str, right: str) -> bool:
    ...


@overload
def timing_safe_compare(left: bytes, right: bytes) -> bool:
    ...


def timing_safe_compare(left: object, right: object) -> bool:
    """
    Compare two strings or two byte strings using hmac.compare_digest.

    Only str and bytes are accepted. Both arguments must have the same accepted
    type, otherwise TypeError is raised.
    """
    left_is_str = isinstance(left, str)
    left_is_bytes = isinstance(left, bytes)
    right_is_str = isinstance(right, str)
    right_is_bytes = isinstance(right, bytes)

    left_is_accepted = left_is_str or left_is_bytes
    right_is_accepted = right_is_str or right_is_bytes

    if not left_is_accepted:
        raise TypeError("left must be str or bytes")

    if not right_is_accepted:
        raise TypeError("right must be str or bytes")

    if type(left) is not type(right):
        raise TypeError("left and right must have the same type")

    return hmac.compare_digest(left, right)