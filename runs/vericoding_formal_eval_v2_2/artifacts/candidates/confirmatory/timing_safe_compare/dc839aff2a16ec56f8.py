import hmac
from typing import Union

ComparableValue = Union[str, bytes]


def timing_safe_compare(left: ComparableValue, right: ComparableValue) -> bool:
    """
    Compare two str or bytes values using hmac.compare_digest.

    Both inputs must be exactly the same supported type: str with str, or bytes
    with bytes. Unsupported types and mixed types raise TypeError.
    """
    left_type = type(left)
    right_type = type(right)

    if left_type is not right_type:
        raise TypeError("timing_safe_compare requires both inputs to have the same type")

    if left_type is not str and left_type is not bytes:
        raise TypeError("timing_safe_compare accepts only str or bytes")

    return hmac.compare_digest(left, right)