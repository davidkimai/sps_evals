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
                d_2_seg_: _dafny.Map
                d_2_seg_ = (segments)[d_1_seg__name_]
                d_3_merged_: _dafny.Map
                d_3_merged_ = result
                d_4_keys_: _dafny.Set
                d_4_keys_ = (d_2_seg_).keys
                d_5_seg__seq_: _dafny.Seq
                out0_: _dafny.Seq
                out0_ = default__.SetToSeq(d_4_keys_)
                d_5_seg__seq_ = out0_
                d_6_j_: int
                d_6_j_ = 0
                while (d_6_j_) < (len(d_5_seg__seq_)):
                    d_7_key_: _dafny.Seq
                    d_7_key_ = (d_5_seg__seq_)[d_6_j_]
                    d_3_merged_ = (d_3_merged_).set(d_7_key_, (d_2_seg_)[d_7_key_])
                    d_6_j_ = (d_6_j_) + (1)
                result = d_3_merged_
            d_0_i_ = (d_0_i_) + (1)
        d_8_override__keys_: _dafny.Set
        d_8_override__keys_ = (user__overrides).keys
        d_9_override__seq_: _dafny.Seq
        out1_: _dafny.Seq
        out1_ = default__.SetToSeq(d_8_override__keys_)
        d_9_override__seq_ = out1_
        d_10_k_: int
        d_10_k_ = 0
        while (d_10_k_) < (len(d_9_override__seq_)):
            d_11_key_: _dafny.Seq
            d_11_key_ = (d_9_override__seq_)[d_10_k_]
            result = (result).set(d_11_key_, (user__overrides)[d_11_key_])
            d_10_k_ = (d_10_k_) + (1)
        return result

    @staticmethod
    def SetToSeq(s):
        result: _dafny.Seq = _dafny.Seq({})
        result = _dafny.SeqWithoutIsStrInference([])
        d_0_remaining_: _dafny.Set
        d_0_remaining_ = s
        while (d_0_remaining_) != (_dafny.Set({})):
            d_1_x_: TypeVar('T__')
            with _dafny.label("_ASSIGN_SUCH_THAT_d_0"):
                assign_such_that_0_: TypeVar('T__')
                for assign_such_that_0_ in (d_0_remaining_).Elements:
                    d_1_x_ = assign_such_that_0_
                    if (d_1_x_) in (d_0_remaining_):
                        raise _dafny.Break("_ASSIGN_SUCH_THAT_d_0")
                raise Exception("assign-such-that search produced no value")
                pass
            result = (result) + (_dafny.SeqWithoutIsStrInference([d_1_x_]))
            d_0_remaining_ = (d_0_remaining_) - (_dafny.Set({d_1_x_}))
        return result

