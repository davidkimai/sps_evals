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
    def ResourceScope(resources):
        closed: _dafny.Seq = _dafny.Seq({})
        d_0_acquired_: _dafny.Seq
        d_0_acquired_ = _dafny.SeqWithoutIsStrInference([])
        d_1_i_: int
        d_1_i_ = 0
        while (d_1_i_) < (len(resources)):
            d_0_acquired_ = (d_0_acquired_) + (_dafny.SeqWithoutIsStrInference([(resources)[d_1_i_]]))
            d_1_i_ = (d_1_i_) + (1)
        d_2_result_: _dafny.Seq
        d_2_result_ = _dafny.SeqWithoutIsStrInference([])
        d_3_j_: int
        d_3_j_ = len(d_0_acquired_)
        while (d_3_j_) > (0):
            d_3_j_ = (d_3_j_) - (1)
            d_2_result_ = (_dafny.SeqWithoutIsStrInference([(d_0_acquired_)[d_3_j_]])) + (d_2_result_)
        closed = d_2_result_
        return closed

