import hmac
from typing import Union


def timing_safe_compare(left: Union[str, bytes], right: Union[str, bytes]) -> bool:
    if not isinstance(left, (str, bytes)) or not isinstance(right, (str, bytes)):
        raise TypeError("timing_safe_compare accepts only str or bytes")
    if type(left) is not type(right):
        raise TypeError("timing_safe_compare requires both inputs to have the same type")
    return hmac.compare_digest(left, right)