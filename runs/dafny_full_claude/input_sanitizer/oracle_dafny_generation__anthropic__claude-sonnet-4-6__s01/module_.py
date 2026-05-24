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
    def sanitize__fields(fields, allowed):
        result: _dafny.Seq = _dafny.Seq({})
        result = _dafny.SeqWithoutIsStrInference([])
        d_0_seen_: _dafny.Set
        d_0_seen_ = _dafny.Set({})
        d_1_i_: int
        d_1_i_ = 0
        while (d_1_i_) < (len(fields)):
            d_2_field_: _dafny.Seq
            d_2_field_ = (fields)[d_1_i_]
            if (((d_2_field_) in (allowed)) and ((d_2_field_) not in (d_0_seen_))) and (default__.is__valid__field(d_2_field_)):
                result = (result) + (_dafny.SeqWithoutIsStrInference([d_2_field_]))
                d_0_seen_ = (d_0_seen_) | (_dafny.Set({d_2_field_}))
            d_1_i_ = (d_1_i_) + (1)
        return result

    @staticmethod
    def is__valid__field(s):
        def lambda0_(forall_var_0_):
            d_0_c_: str = forall_var_0_
            return not ((d_0_c_) in (s)) or (default__.is__valid__char(d_0_c_))

        return _dafny.quantifier((s).UniqueElements, True, lambda0_)

    @staticmethod
    def is__valid__char(c):
        return (((((_dafny.CodePoint('a')) <= (c)) and ((c) <= (_dafny.CodePoint('z')))) or (((_dafny.CodePoint('A')) <= (c)) and ((c) <= (_dafny.CodePoint('Z'))))) or (((_dafny.CodePoint('0')) <= (c)) and ((c) <= (_dafny.CodePoint('9'))))) or ((c) == (_dafny.CodePoint('_')))

