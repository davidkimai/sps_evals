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
    def collect__cursor__items(pages):
        result: _dafny.Seq = _dafny.Seq({})
        result = _dafny.SeqWithoutIsStrInference([])
        d_0_i_: int
        d_0_i_ = 0
        while (d_0_i_) < (len(pages)):
            result = (result) + ((pages)[d_0_i_])
            d_0_i_ = (d_0_i_) + (1)
        return result

