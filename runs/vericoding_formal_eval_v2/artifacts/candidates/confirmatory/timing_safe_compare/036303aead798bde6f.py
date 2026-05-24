from __future__ import annotations

import hmac
from typing import Union


def timing_safe_compare(left: Union[str, bytes], right: Union[str, bytes]) -> bool:
    if type(left) is not type(right):
        raise TypeError("left and right must have the same type")
    if not isinstance(left, (str, bytes)):
        raise TypeError("left and right must be str or bytes")
    return hmac.compare_digest(left, right)