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
    def resolve__flags(defaults, segments, user, user__overrides, user__segments):
        result: _dafny.Map = _dafny.Map({})
        result = defaults
        d_0_i_: int
        d_0_i_ = 0
        while (d_0_i_) < (len(user__segments)):
            d_1_seg__name_: _dafny.Seq
            d_1_seg__name_ = (user__segments)[d_0_i_]
            if (d_1_seg__name_) in (segments):
                d_2_seg__flags_: _dafny.Map
                d_2_seg__flags_ = (segments)[d_1_seg__name_]
                d_3_keys_: _dafny.Set
                d_3_keys_ = (d_2_seg__flags_).keys
                result = (result) | (d_2_seg__flags_)
            d_0_i_ = (d_0_i_) + (1)
        result = (result) | (user__overrides)
        return result

