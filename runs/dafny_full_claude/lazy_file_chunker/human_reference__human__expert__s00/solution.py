from __future__ import annotations

from collections.abc import Iterator
from typing import BinaryIO


def iter_file_chunks(file_obj: BinaryIO, chunk_size: int) -> Iterator[bytes]:
    if chunk_size <= 0:
        raise ValueError('chunk_size must be positive')
    while True:
        chunk = file_obj.read(chunk_size)
        if not chunk:
            break
        yield chunk
