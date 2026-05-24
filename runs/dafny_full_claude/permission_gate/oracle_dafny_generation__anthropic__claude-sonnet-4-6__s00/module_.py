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
    def has__permission(matrix, role, permission):
        result: bool = False
        if (role) in (matrix):
            d_0_perms_: _dafny.Set
            d_0_perms_ = (matrix)[role]
            if (permission) in (d_0_perms_):
                result = True
            elif True:
                result = False
        elif True:
            result = False
        return result

