from __future__ import annotations

import hmac


def timing_safe_compare(left: str | bytes, right: str | bytes) -> bool:
    if not isinstance(left, (str, bytes)) or not isinstance(right, (str, bytes)):
        raise TypeError('values must be str or bytes')
    if type(left) is not type(right):
        raise TypeError('values must share a type')
    return hmac.compare_digest(left, right)
