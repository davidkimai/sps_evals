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
    def check__access(role, permission, matrix, log):
        allowed: bool = False
        newLog: _dafny.Seq = _dafny.Seq({})
        allowed = False
        if (role) in (matrix):
            d_0_perms_: _dafny.Set
            d_0_perms_ = (matrix)[role]
            if (permission) in (d_0_perms_):
                allowed = True
        d_1_allowedStr_: _dafny.Seq
        if allowed:
            d_1_allowedStr_ = _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "true"))
        elif True:
            d_1_allowedStr_ = _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "false"))
        d_2_entry_: _dafny.Map
        d_2_entry_ = _dafny.Map({_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "role")): role, _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "permission")): permission, _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "allowed")): d_1_allowedStr_})
        newLog = (log) + (_dafny.SeqWithoutIsStrInference([d_2_entry_]))
        return allowed, newLog

