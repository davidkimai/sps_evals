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
    def AuditLogWriter(sink, initialSize):
        log: _dafny.Array = _dafny.Array(None, 0)
        nw0_ = _dafny.Array((int(0), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "")), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, ""))), initialSize)
        log = nw0_
        return log

    @staticmethod
    def Write(sink, count, actor, action):
        newSink: _dafny.Array = _dafny.Array(None, 0)
        newCount: int = int(0)
        record: tuple = (int(0), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "")), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "")))
        d_0_seq__num_: int
        d_0_seq__num_ = (count) + (1)
        record = (d_0_seq__num_, actor, action)
        if (count) < ((sink).length(0)):
            nw0_ = _dafny.Array((int(0), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "")), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, ""))), (sink).length(0))
            newSink = nw0_
            d_1_i_: int
            d_1_i_ = 0
            while (d_1_i_) < (count):
                (newSink)[(d_1_i_)] = (sink)[d_1_i_]
                d_1_i_ = (d_1_i_) + (1)
            (newSink)[(count)] = record
            newCount = (count) + (1)
        elif True:
            d_2_newSize_: int
            if ((sink).length(0)) == (0):
                d_2_newSize_ = 4
            elif True:
                d_2_newSize_ = ((sink).length(0)) * (2)
            nw1_ = _dafny.Array((int(0), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "")), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, ""))), d_2_newSize_)
            newSink = nw1_
            d_3_i_: int
            d_3_i_ = 0
            while (d_3_i_) < (count):
                (newSink)[(d_3_i_)] = (sink)[d_3_i_]
                d_3_i_ = (d_3_i_) + (1)
            (newSink)[(count)] = record
            newCount = (count) + (1)
        return newSink, newCount, record

