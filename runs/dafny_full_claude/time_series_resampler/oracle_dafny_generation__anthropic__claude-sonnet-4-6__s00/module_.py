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
    def resample__series(points, start, end, interval):
        result: _dafny.Seq = _dafny.Seq({})
        result = _dafny.SeqWithoutIsStrInference([])
        d_0_ts_: int
        d_0_ts_ = start
        while (d_0_ts_) <= (end):
            d_1_best__val_: _dafny.BigRational
            d_1_best__val_ = _dafny.BigRational('0e0')
            d_2_found_: bool
            d_2_found_ = False
            d_3_i_: int
            d_3_i_ = 0
            while (d_3_i_) < (len(points)):
                d_4_pt__time_: int
                d_4_pt__time_ = ((points)[d_3_i_])[0]
                d_5_pt__val_: _dafny.BigRational
                d_5_pt__val_ = ((points)[d_3_i_])[1]
                if (d_4_pt__time_) <= (d_0_ts_):
                    if not(d_2_found_):
                        d_1_best__val_ = d_5_pt__val_
                        d_2_found_ = True
                    elif True:
                        d_1_best__val_ = d_5_pt__val_
                d_3_i_ = (d_3_i_) + (1)
            d_6_best__time_: int
            d_6_best__time_ = 0
            d_1_best__val_ = _dafny.BigRational('0e0')
            d_2_found_ = False
            d_3_i_ = 0
            while (d_3_i_) < (len(points)):
                d_7_pt__time_: int
                d_7_pt__time_ = ((points)[d_3_i_])[0]
                d_8_pt__val_: _dafny.BigRational
                d_8_pt__val_ = ((points)[d_3_i_])[1]
                if (d_7_pt__time_) <= (d_0_ts_):
                    if (not(d_2_found_)) or ((d_7_pt__time_) >= (d_6_best__time_)):
                        d_6_best__time_ = d_7_pt__time_
                        d_1_best__val_ = d_8_pt__val_
                        d_2_found_ = True
                d_3_i_ = (d_3_i_) + (1)
            if d_2_found_:
                result = (result) + (_dafny.SeqWithoutIsStrInference([(d_0_ts_, d_1_best__val_)]))
            elif True:
                result = (result) + (_dafny.SeqWithoutIsStrInference([(d_0_ts_, _dafny.BigRational('0e0'))]))
            d_0_ts_ = (d_0_ts_) + (interval)
        return result

    @staticmethod
    def resample__series__with__flags(points, start, end, interval):
        result: _dafny.Seq = _dafny.Seq({})
        valid: _dafny.Seq = _dafny.Seq({})
        result = _dafny.SeqWithoutIsStrInference([])
        valid = _dafny.SeqWithoutIsStrInference([])
        d_0_ts_: int
        d_0_ts_ = start
        while (d_0_ts_) <= (end):
            d_1_best__time_: int
            d_1_best__time_ = 0
            d_2_best__val_: _dafny.BigRational
            d_2_best__val_ = _dafny.BigRational('0e0')
            d_3_found_: bool
            d_3_found_ = False
            d_4_i_: int
            d_4_i_ = 0
            while (d_4_i_) < (len(points)):
                d_5_pt__time_: int
                d_5_pt__time_ = ((points)[d_4_i_])[0]
                d_6_pt__val_: _dafny.BigRational
                d_6_pt__val_ = ((points)[d_4_i_])[1]
                if (d_5_pt__time_) <= (d_0_ts_):
                    if (not(d_3_found_)) or ((d_5_pt__time_) >= (d_1_best__time_)):
                        d_1_best__time_ = d_5_pt__time_
                        d_2_best__val_ = d_6_pt__val_
                        d_3_found_ = True
                d_4_i_ = (d_4_i_) + (1)
            result = (result) + (_dafny.SeqWithoutIsStrInference([(d_0_ts_, d_2_best__val_)]))
            valid = (valid) + (_dafny.SeqWithoutIsStrInference([d_3_found_]))
            d_0_ts_ = (d_0_ts_) + (interval)
        return result, valid

