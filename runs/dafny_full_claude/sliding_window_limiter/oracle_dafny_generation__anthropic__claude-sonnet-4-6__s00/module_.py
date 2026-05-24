import sys
from typing import Callable, Any, TypeVar, NamedTuple
from math import floor
from itertools import count

import module_ as module_
import _dafny as _dafny
import System_ as System_

# Module: module_


class SlidingWindowLimiter:
    def  __init__(self):
        self.limit: int = int(0)
        self.window__seconds: int = int(0)
        self.timestamps: _dafny.Map = _dafny.Map({})
        pass

    def __dafnystr__(self) -> str:
        return "_module.SlidingWindowLimiter"
    def ctor__(self, limit, window__seconds):
        (self).limit = limit
        (self).window__seconds = window__seconds
        (self).timestamps = _dafny.Map({})

    def allow(self, key, timestamp):
        result: bool = False
        d_0_existing_: _dafny.Seq
        d_0_existing_ = _dafny.SeqWithoutIsStrInference([])
        if (key) in (self.timestamps):
            d_0_existing_ = (self.timestamps)[key]
        d_1_filtered_: _dafny.Seq
        d_1_filtered_ = _dafny.SeqWithoutIsStrInference([])
        d_2_i_: int
        d_2_i_ = 0
        while (d_2_i_) < (len(d_0_existing_)):
            if (((d_0_existing_)[d_2_i_]) > ((timestamp) - (self.window__seconds))) and (((d_0_existing_)[d_2_i_]) <= (timestamp)):
                d_1_filtered_ = (d_1_filtered_) + (_dafny.SeqWithoutIsStrInference([(d_0_existing_)[d_2_i_]]))
            d_2_i_ = (d_2_i_) + (1)
        if (len(d_1_filtered_)) < (self.limit):
            d_3_newSeq_: _dafny.Seq
            d_3_newSeq_ = (d_1_filtered_) + (_dafny.SeqWithoutIsStrInference([timestamp]))
            (self).timestamps = (self.timestamps).set(key, d_3_newSeq_)
            result = True
        elif True:
            (self).timestamps = (self.timestamps).set(key, d_1_filtered_)
            result = False
        return result

    def snapshot(self, key):
        result: _dafny.Seq = _dafny.Seq({})
        if (key) in (self.timestamps):
            result = (self.timestamps)[key]
        elif True:
            result = _dafny.SeqWithoutIsStrInference([])
        return result

