import hmac
from typing import Union


def timing_safe_compare(left: Union[str, bytes], right: Union[str, bytes]) -> bool:
    if type(left) not in (str, bytes):
        raise TypeError("left must be str or bytes")
    if type(right) not in (str, bytes):
        raise TypeError("right must be str or bytes")
    if type(left) is not type(right):
        raise TypeError("left and right must have the same type")

    return bool(hmac.compare_digest(left, right))