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
    def HandleUnderspecified(mode, value, hasMode, hasValue):
        result: int = int(0)
        success: bool = False
        if ((hasMode) and (hasValue)) and ((mode) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "echo")))):
            result = value
            success = True
        elif True:
            result = 0
            success = False
        return result, success

    @staticmethod
    def Main(noArgsParameter__):
        d_0_result_: int
        d_1_success_: bool
        out0_: int
        out1_: bool
        out0_, out1_ = default__.HandleUnderspecified(_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "echo")), 42, True, True)
        d_0_result_ = out0_
        d_1_success_ = out1_
        d_2_result2_: int
        d_3_success2_: bool
        out2_: int
        out3_: bool
        out2_, out3_ = default__.HandleUnderspecified(_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "other")), 42, True, True)
        d_2_result2_ = out2_
        d_3_success2_ = out3_
        d_4_result3_: int
        d_5_success3_: bool
        out4_: int
        out5_: bool
        out4_, out5_ = default__.HandleUnderspecified(_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "echo")), 10, False, True)
        d_4_result3_ = out4_
        d_5_success3_ = out5_

