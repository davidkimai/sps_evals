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
    def resolve__flags(defaults, segments, user, user__overrides):
        result: _dafny.Map = _dafny.Map({})
        result = defaults
        if (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "segments"))) in (user):
            d_0_seg__list_: _dafny.Seq
            d_0_seg__list_ = (user)[_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "segments"))]
            d_1_i_: int
            d_1_i_ = 0
            while (d_1_i_) < (len(d_0_seg__list_)):
                d_2_seg__name_: _dafny.Seq
                d_2_seg__name_ = (d_0_seg__list_)[d_1_i_]
                if (d_2_seg__name_) in (segments):
                    d_3_seg__overrides_: _dafny.Map
                    d_3_seg__overrides_ = (segments)[d_2_seg__name_]
                    d_4_keys_: _dafny.Set
                    d_4_keys_ = (d_3_seg__overrides_).keys
                    d_5_ks_: _dafny.Set
                    def iife0_():
                        coll0_ = _dafny.Set()
                        compr_0_: _dafny.Seq
                        for compr_0_ in (d_4_keys_).Elements:
                            d_6_k_: _dafny.Seq = compr_0_
                            if (d_6_k_) in (d_4_keys_):
                                coll0_ = coll0_.union(_dafny.Set([d_6_k_]))
                        return _dafny.Set(coll0_)
                    d_5_ks_ = iife0_()
                    
                    d_7_ks__seq_: _dafny.Seq
                    d_7_ks__seq_ = _dafny.SeqWithoutIsStrInference([])
                    d_8_remaining_: _dafny.Set
                    d_8_remaining_ = d_5_ks_
                    while (len(d_8_remaining_)) > (0):
                        d_9_k_: _dafny.Seq
                        with _dafny.label("_ASSIGN_SUCH_THAT_d_0"):
                            assign_such_that_0_: _dafny.Seq
                            for assign_such_that_0_ in (d_8_remaining_).Elements:
                                d_9_k_ = assign_such_that_0_
                                if (d_9_k_) in (d_8_remaining_):
                                    raise _dafny.Break("_ASSIGN_SUCH_THAT_d_0")
                            raise Exception("assign-such-that search produced no value")
                            pass
                        result = (result).set(d_9_k_, (d_3_seg__overrides_)[d_9_k_])
                        d_8_remaining_ = (d_8_remaining_) - (_dafny.Set({d_9_k_}))
                d_1_i_ = (d_1_i_) + (1)
        d_10_override__keys_: _dafny.Set
        d_10_override__keys_ = (user__overrides).keys
        d_11_remaining2_: _dafny.Set
        def iife1_():
            coll1_ = _dafny.Set()
            compr_1_: _dafny.Seq
            for compr_1_ in (d_10_override__keys_).Elements:
                d_12_k_: _dafny.Seq = compr_1_
                if (d_12_k_) in (d_10_override__keys_):
                    coll1_ = coll1_.union(_dafny.Set([d_12_k_]))
            return _dafny.Set(coll1_)
        d_11_remaining2_ = iife1_()
        
        while (len(d_11_remaining2_)) > (0):
            d_13_k_: _dafny.Seq
            with _dafny.label("_ASSIGN_SUCH_THAT_d_1"):
                assign_such_that_1_: _dafny.Seq
                for assign_such_that_1_ in (d_11_remaining2_).Elements:
                    d_13_k_ = assign_such_that_1_
                    if (d_13_k_) in (d_11_remaining2_):
                        raise _dafny.Break("_ASSIGN_SUCH_THAT_d_1")
                raise Exception("assign-such-that search produced no value")
                pass
            result = (result).set(d_13_k_, (user__overrides)[d_13_k_])
            d_11_remaining2_ = (d_11_remaining2_) - (_dafny.Set({d_13_k_}))
        return result

