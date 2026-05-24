def timing_safe_compare(left, right, pad_to_length: int | None = None, pad_char: str = "\0") -> bool:
    if not isinstance(left, (str, bytes)) or not isinstance(right, (str, bytes)):
        raise TypeError("left and right must be str or bytes")

    if type(left) is not type(right):
        raise TypeError("left and right must have the same type")

    if pad_to_length is None:
        return left == right

    if isinstance(left, bytes):
        raise TypeError("padding is supported only for strings")

    if not isinstance(pad_char, str) or len(pad_char) != 1:
        raise ValueError("pad_char must be exactly one character")

    return left.ljust(pad_to_length, pad_char) == right.ljust(pad_to_length, pad_char)