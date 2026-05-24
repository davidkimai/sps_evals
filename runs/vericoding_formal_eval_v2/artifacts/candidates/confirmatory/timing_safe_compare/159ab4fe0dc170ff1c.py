import hmac
from typing import Union

ComparableValue = Union[str, bytes]


def _is_supported_value(value: object) -> bool:
    return isinstance(value, (str, bytes))


def _validate_inputs(left: object, right: object) -> None:
    if not _is_supported_value(left):
        raise TypeError("left must be str or bytes")
    if not _is_supported_value(right):
        raise TypeError("right must be str or bytes")
    if type(left) is not type(right):
        raise TypeError("left and right must have the same type")


def timing_safe_compare(left: ComparableValue, right: ComparableValue) -> bool:
    _validate_inputs(left, right)
    return bool(hmac.compare_digest(left, right))