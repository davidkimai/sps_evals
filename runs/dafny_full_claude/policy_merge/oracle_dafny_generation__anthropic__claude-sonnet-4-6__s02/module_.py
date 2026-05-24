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
    def merge__policy(defaults, override):
        result: _dafny.Map = _dafny.Map({})
        result = defaults
        d_0_overrideKeys_: _dafny.Set
        d_0_overrideKeys_ = (override).keys
        while (d_0_overrideKeys_) != (_dafny.Set({})):
            d_1_k_: _dafny.Seq
            with _dafny.label("_ASSIGN_SUCH_THAT_d_0"):
                assign_such_that_0_: _dafny.Seq
                for assign_such_that_0_ in (d_0_overrideKeys_).Elements:
                    d_1_k_ = assign_such_that_0_
                    if (d_1_k_) in (d_0_overrideKeys_):
                        raise _dafny.Break("_ASSIGN_SUCH_THAT_d_0")
                raise Exception("assign-such-that search produced no value")
                pass
            d_0_overrideKeys_ = (d_0_overrideKeys_) - (_dafny.Set({d_1_k_}))
            if ((override)[d_1_k_]) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "None"))):
                if (d_1_k_) in (result):
                    result = (result) - (_dafny.Set({d_1_k_}))
            elif True:
                result = (result).set(d_1_k_, (override)[d_1_k_])
        return result

