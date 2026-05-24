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
    def timing__safe__compare(left, right):
        result: bool = False
        if (len(left)) != (len(right)):
            result = False
            return result
        d_0_diff_: int
        d_0_diff_ = 0
        d_1_i_: int
        d_1_i_ = 0
        while (d_1_i_) < (len(left)):
            if ((left)[d_1_i_]) != ((right)[d_1_i_]):
                d_0_diff_ = (d_0_diff_) + (1)
            d_1_i_ = (d_1_i_) + (1)
        result = (d_0_diff_) == (0)
        return result

