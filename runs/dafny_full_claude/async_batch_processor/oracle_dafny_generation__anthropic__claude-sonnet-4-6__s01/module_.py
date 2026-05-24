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
    def process__in__batches(items, batch__size, concurrency):
        result: _dafny.Seq = _dafny.Seq({})
        result = _dafny.SeqWithoutIsStrInference([])
        d_0_i_: int
        d_0_i_ = 0
        while (d_0_i_) < (len(items)):
            d_1_end_: int
            d_1_end_ = (d_0_i_) + (batch__size)
            if (d_1_end_) > (len(items)):
                d_1_end_ = len(items)
            d_2_batch_: _dafny.Seq
            d_2_batch_ = _dafny.SeqWithoutIsStrInference((items)[d_0_i_:d_1_end_:])
            result = (result) + (d_2_batch_)
            d_0_i_ = d_1_end_
        return result

