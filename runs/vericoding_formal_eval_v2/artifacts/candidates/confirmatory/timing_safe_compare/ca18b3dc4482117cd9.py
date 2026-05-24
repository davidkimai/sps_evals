import hmac
from typing import Union

ComparableDigest = Union[str, bytes]


def timing_safe_compare(left: ComparableDigest, right: ComparableDigest) -> bool:
    if type(left) is not type(right):
        raise TypeError("left and right must have the same type")

    if type(left) not in (str, bytes):
        raise TypeError("left and right must be str or bytes")

    return bool(hmac.compare_digest(left, right))