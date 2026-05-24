import hmac
from typing import Union

TimingSafeComparable = Union[str, bytes]


def timing_safe_compare(left: TimingSafeComparable, right: TimingSafeComparable) -> bool:
    """
    Compare two strings or two bytes objects using hmac.compare_digest.

    Both arguments must be str or bytes, and both must have the same concrete
    type. A TypeError is raised otherwise.
    """
    if not isinstance(left, (str, bytes)) or not isinstance(right, (str, bytes)):
        raise TypeError("timing_safe_compare accepts only str or bytes")

    if type(left) is not type(right):
        raise TypeError("left and right must have the same type")

    return hmac.compare_digest(left, right)