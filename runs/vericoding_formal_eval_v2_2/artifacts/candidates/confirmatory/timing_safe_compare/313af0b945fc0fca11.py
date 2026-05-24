from typing import Optional


def timing_safe_compare(left, right, pad_to_length: int | None = None, pad_char: str = "\0") -> bool:
    if type(left) is not type(right):
        raise TypeError("left and right must have the same type")

    if isinstance(left, bytes):
        if pad_to_length is not None:
            raise TypeError("padding is supported only for strings")
        if not isinstance(left, bytes) or not isinstance(right, bytes):
            raise TypeError("inputs must be str or bytes")
        return left == right

    if isinstance(left, str):
        if pad_to_length is None:
            return left == right

        if not isinstance(pad_char, str) or len(pad_char) != 1:
            raise ValueError("pad_char must be exactly one character")

        if not isinstance(pad_to_length, int):
            raise TypeError("pad_to_length must be an int or None")

        if len(left) < pad_to_length:
            left = left.ljust(pad_to_length, pad_char)
        if len(right) < pad_to_length:
            right = right.ljust(pad_to_length, pad_char)
        return left == right

    raise TypeError("inputs must be str or bytes")