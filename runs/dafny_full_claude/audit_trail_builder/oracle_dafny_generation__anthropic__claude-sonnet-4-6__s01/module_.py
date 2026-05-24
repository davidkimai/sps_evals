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
    def build__audit__trail(events):
        result: _dafny.Seq = _dafny.Seq({})
        d_0_trail_: _dafny.Seq
        d_0_trail_ = _dafny.SeqWithoutIsStrInference([])
        d_1_seq__num_: int
        d_1_seq__num_ = 1
        hi0_ = len(events)
        for d_2_i_ in range(0, hi0_):
            d_3_event_: _dafny.Map
            d_3_event_ = (events)[d_2_i_]
            if ((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "source_system"))) in (d_3_event_)) and ((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "actor_id"))) in (d_3_event_)):
                d_4_record_: _dafny.Map
                d_4_record_ = _dafny.Map({_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "sequence")): default__.int__to__string(d_1_seq__num_), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "source_system")): (d_3_event_)[_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "source_system"))], _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "actor_id")): (d_3_event_)[_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "actor_id"))], _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "action")): ((d_3_event_)[_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "action"))] if (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "action"))) in (d_3_event_) else _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "")))})
                d_0_trail_ = (d_0_trail_) + (_dafny.SeqWithoutIsStrInference([d_4_record_]))
                d_1_seq__num_ = (d_1_seq__num_) + (1)
        result = d_0_trail_
        return result

    @staticmethod
    def int__to__string(n):
        if (n) == (0):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "0"))
        elif (n) == (1):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "1"))
        elif (n) == (2):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "2"))
        elif (n) == (3):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "3"))
        elif (n) == (4):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "4"))
        elif (n) == (5):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "5"))
        elif (n) == (6):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "6"))
        elif (n) == (7):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "7"))
        elif (n) == (8):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "8"))
        elif (n) == (9):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "9"))
        elif True:
            return (default__.int__to__string(_dafny.euclidian_division(n, 10))) + (default__.int__to__string(_dafny.euclidian_modulus(n, 10)))

