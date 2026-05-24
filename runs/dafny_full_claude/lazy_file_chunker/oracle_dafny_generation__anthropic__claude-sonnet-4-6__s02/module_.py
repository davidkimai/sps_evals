import sys
from typing import Callable, Any, TypeVar, NamedTuple
from math import floor
from itertools import count

import module_ as module_
import _dafny as _dafny
import System_ as System_

# Module: module_

class default__:
    def  __init__(self):
        pass

    @staticmethod
    def iter__file__chunks(file__obj, chunk__size):
        chunks: _dafny.Seq = _dafny.Seq({})
        chunks = _dafny.SeqWithoutIsStrInference([])
        return chunks

    @staticmethod
    def ValidateChunkSize(chunk__size):
        pass
        pass

    @staticmethod
    def ReadChunk(data, offset, chunk__size):
        chunk: _dafny.Seq = _dafny.Seq({})
        if ((offset) + (chunk__size)) <= (len(data)):
            chunk = _dafny.SeqWithoutIsStrInference((data)[offset:(offset) + (chunk__size):])
        elif True:
            chunk = _dafny.SeqWithoutIsStrInference((data)[offset::])
        return chunk

    @staticmethod
    def SplitIntoChunks(data, chunk__size):
        chunks: _dafny.Seq = _dafny.Seq({})
        chunks = _dafny.SeqWithoutIsStrInference([])
        d_0_offset_: int
        d_0_offset_ = 0
        while (d_0_offset_) < (len(data)):
            d_1_end_: int
            d_1_end_ = (d_0_offset_) + (chunk__size)
            if (d_1_end_) > (len(data)):
                d_1_end_ = len(data)
            d_2_chunk_: _dafny.Seq
            d_2_chunk_ = _dafny.SeqWithoutIsStrInference((data)[d_0_offset_:d_1_end_:])
            chunks = (chunks) + (_dafny.SeqWithoutIsStrInference([d_2_chunk_]))
            d_0_offset_ = d_1_end_
        return chunks

