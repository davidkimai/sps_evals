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
    def build__user__purchase__index(events):
        result: _dafny.Map = _dafny.Map({})
        result = _dafny.Map({})
        d_0_i_: int
        d_0_i_ = 0
        while (d_0_i_) < (len(events)):
            d_1_event_: _dafny.Map
            d_1_event_ = (events)[d_0_i_]
            if (((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "user_id"))) in (d_1_event_)) and ((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "kind"))) in (d_1_event_))) and ((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "amount"))) in (d_1_event_)):
                d_2_user__id_: _dafny.Seq
                d_2_user__id_ = (d_1_event_)[_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "user_id"))]
                d_3_kind_: _dafny.Seq
                d_3_kind_ = (d_1_event_)[_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "kind"))]
                d_4_amount__str_: _dafny.Seq
                d_4_amount__str_ = (d_1_event_)[_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "amount"))]
                if ((d_3_kind_) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "purchase")))) and ((len(d_2_user__id_)) > (0)):
                    d_5_amount_: Option
                    d_5_amount_ = default__.parse__int(d_4_amount__str_)
                    if (d_5_amount_).is_Some:
                        if (d_2_user__id_) in (result):
                            d_6_old__count_: int
                            d_6_old__count_ = ((result)[d_2_user__id_])[_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "count"))]
                            d_7_old__total_: int
                            d_7_old__total_ = ((result)[d_2_user__id_])[_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "total"))]
                            result = (result).set(d_2_user__id_, _dafny.Map({_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "count")): (d_6_old__count_) + (1), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "total")): (d_7_old__total_) + ((d_5_amount_).value)}))
                        elif True:
                            result = (result).set(d_2_user__id_, _dafny.Map({_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "count")): 1, _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "total")): (d_5_amount_).value}))
            d_0_i_ = (d_0_i_) + (1)
        return result

    @staticmethod
    def parse__int(s):
        if (len(s)) == (0):
            return Option_None()
        elif ((s)[0]) == (_dafny.CodePoint('-')):
            if (len(s)) == (1):
                return Option_None()
            elif True:
                d_0_rest_ = default__.parse__nat(_dafny.SeqWithoutIsStrInference((s)[1::]))
                if (d_0_rest_).is_Some:
                    return Option_Some((0) - ((d_0_rest_).value))
                elif True:
                    return Option_None()
        elif True:
            d_1_n_ = default__.parse__nat(s)
            if (d_1_n_).is_Some:
                return Option_Some((d_1_n_).value)
            elif True:
                return Option_None()

    @staticmethod
    def parse__nat(s):
        if (len(s)) == (0):
            return Option_None()
        elif True:
            return default__.parse__nat__helper(s, 0, 0)

    @staticmethod
    def parse__nat__helper(s, idx, acc):
        while True:
            with _dafny.label():
                if (idx) == (len(s)):
                    if (idx) == (0):
                        return Option_None()
                    elif True:
                        return Option_Some(acc)
                elif True:
                    d_0_c_ = (s)[idx]
                    if ((_dafny.CodePoint('0')) <= (d_0_c_)) and ((d_0_c_) <= (_dafny.CodePoint('9'))):
                        in0_ = s
                        in1_ = (idx) + (1)
                        in2_ = ((acc) * (10)) + ((ord(d_0_c_)) - (ord(_dafny.CodePoint('0'))))
                        s = in0_
                        idx = in1_
                        acc = in2_
                        raise _dafny.TailCall()
                    elif True:
                        return Option_None()
                break


class Option:
    @classmethod
    def default(cls, ):
        return lambda: Option_None()
    def __ne__(self, __o: object) -> bool:
        return not self.__eq__(__o)
    @property
    def is_None(self) -> bool:
        return isinstance(self, Option_None)
    @property
    def is_Some(self) -> bool:
        return isinstance(self, Option_Some)

class Option_None(Option, NamedTuple('None_', [])):
    def __dafnystr__(self) -> str:
        return f'Option.None'
    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, Option_None)
    def __hash__(self) -> int:
        return super().__hash__()

class Option_Some(Option, NamedTuple('Some', [('value', Any)])):
    def __dafnystr__(self) -> str:
        return f'Option.Some({_dafny.string_of(self.value)})'
    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, Option_Some) and self.value == __o.value
    def __hash__(self) -> int:
        return super().__hash__()

