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
        d_1_current_: int
        d_1_current_ = base__seconds
        d_2_i_: int
        d_2_i_ = 0
        while (d_2_i_) < (attempts):
            d_3_delay_: int = int(0)
            if (d_1_current_) > (cap__seconds):
                d_3_delay_ = cap__seconds
            elif True:
                d_3_delay_ = d_1_current_
            d_0_schedule_ = (d_0_schedule_) + (_dafny.SeqWithoutIsStrInference([d_3_delay_]))
            if (d_1_current_) <= (_dafny.euclidian_division(cap__seconds, 2)):
                d_1_current_ = (d_1_current_) * (2)
            elif True:
                d_1_current_ = cap__seconds
            d_2_i_ = (d_2_i_) + (1)
        result = d_0_schedule_
        return result
        return result

