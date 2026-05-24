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
    def transition__state(state, event):
        result: _dafny.Seq = _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, ""))
        if ((state) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "idle")))) and ((event) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "start")))):
            result = _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "running"))
        elif ((state) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "running")))) and ((event) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "stop")))):
            result = _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "idle"))
        elif ((state) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "running")))) and ((event) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "fail")))):
            result = _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "failed"))
        elif ((state) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "failed")))) and ((event) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "reset")))):
            result = _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "idle"))
        elif True:
            result = state
        return result

