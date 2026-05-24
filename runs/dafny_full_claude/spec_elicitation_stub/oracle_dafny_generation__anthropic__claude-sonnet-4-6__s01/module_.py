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
    def handle__underspecified(mode, value, hasMode, hasValue):
        result: int = int(0)
        raised: bool = False
        if ((hasMode) and ((mode) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "echo"))))) and (hasValue):
            result = value
            raised = False
        elif True:
            result = 0
            raised = True
        return result, raised

