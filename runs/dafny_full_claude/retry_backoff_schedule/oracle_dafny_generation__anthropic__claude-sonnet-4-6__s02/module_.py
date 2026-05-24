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
    def build__retry__schedule(attempts, base__seconds, cap__seconds):
        result: _dafny.Seq = _dafny.Seq({})
        if (attempts) == (0):
            result = _dafny.SeqWithoutIsStrInference([])
            return result
        d_0_schedule_: _dafny.Seq
        d_0_schedule_ = _dafny.SeqWithoutIsStrInference([])
        d_1_delay_: int
        d_1_delay_ = base__seconds
        d_2_i_: int
        d_2_i_ = 0
        while (d_2_i_) < (attempts):
            d_3_capped_: int
            if (d_1_delay_) > (cap__seconds):
                d_3_capped_ = cap__seconds
            elif True:
                d_3_capped_ = d_1_delay_
            d_0_schedule_ = (d_0_schedule_) + (_dafny.SeqWithoutIsStrInference([d_3_capped_]))
            if (d_1_delay_) <= (_dafny.euclidian_division(cap__seconds, 2)):
                d_1_delay_ = (d_1_delay_) * (2)
            elif True:
                d_1_delay_ = cap__seconds
            d_2_i_ = (d_2_i_) + (1)
        result = d_0_schedule_
        return result
        return result

    @staticmethod
    def Main(noArgsParameter__):
        d_0_s1_: _dafny.Seq
        out0_: _dafny.Seq
        out0_ = default__.build__retry__schedule(5, 1, 30)
        d_0_s1_ = out0_
        _dafny.print(_dafny.string_of(d_0_s1_))
        _dafny.print((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "\n"))).VerbatimString(False))
        d_1_s2_: _dafny.Seq
        out1_: _dafny.Seq
        out1_ = default__.build__retry__schedule(0, 1, 30)
        d_1_s2_ = out1_
        _dafny.print(_dafny.string_of(d_1_s2_))
        _dafny.print((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "\n"))).VerbatimString(False))
        d_2_s3_: _dafny.Seq
        out2_: _dafny.Seq
        out2_ = default__.build__retry__schedule(3, 10, 25)
        d_2_s3_ = out2_
        _dafny.print(_dafny.string_of(d_2_s3_))
        _dafny.print((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "\n"))).VerbatimString(False))

