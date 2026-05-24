import hmac
from typing import Optional, Union


def timing_safe_compare(left, right, pad_to_length: int | None = None, pad_char: str = '\0') -> bool:
    if type(left) is not type(right):
        raise TypeError("left and right must have the same type")
    if not isinstance(left, (str, bytes)):
        raise TypeError("left and right must be str or bytes")

    if pad_to_length is not None:
        if not isinstance(pad_to_length, int):
            raise TypeError("pad_to_length must be an int or None")
        if pad_to_length < 0:
            raise ValueError("pad_to_length must be non-negative")

    if isinstance(left, str):
        if not isinstance(pad_char, str):
            raise TypeError("pad_char must be a str when comparing strings")
        if len(pad_char) != 1:
            raise ValueError("pad_char must be exactly one character")

        if pad_to_length is not None:
            left = left.ljust(pad_to_length, pad_char)
            right = right.ljust(pad_to_length, pad_char)

        return hmac.compare_digest(left, right)

    if isinstance(left, bytes):
        if pad_char != '\0':
            raise TypeError("pad_char is only supported for string comparisons")

        if pad_to_length is not None:
            pad_byte = b'\0'
            left = left.ljust(pad_to_length, pad_byte)
            right = right.ljust(pad_to_length, pad_byte)

        return hmac.compare_digest(left, right)

    raise TypeError("left and right must be str or bytes")