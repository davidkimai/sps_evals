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
    def reconcile__entries(entries):
        result: _dafny.Map = _dafny.Map({})
        result = _dafny.Map({})
        d_0_i_: int
        d_0_i_ = 0
        while (d_0_i_) < (len(entries)):
            d_1_account_: _dafny.Seq
            d_1_account_ = ((entries)[d_0_i_])[0]
            d_2_direction_: _dafny.Seq
            d_2_direction_ = ((entries)[d_0_i_])[1]
            d_3_amount_: int
            d_3_amount_ = ((entries)[d_0_i_])[2]
            d_4_debit_: int
            d_4_debit_ = 0
            d_5_credit_: int
            d_5_credit_ = 0
            if (d_1_account_) in (result):
                d_4_debit_ = ((result)[d_1_account_])[0]
                d_5_credit_ = ((result)[d_1_account_])[1]
            if (d_2_direction_) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "debit"))):
                d_4_debit_ = (d_4_debit_) + (d_3_amount_)
            elif True:
                d_5_credit_ = (d_5_credit_) + (d_3_amount_)
            d_6_balance_: int
            d_6_balance_ = (d_5_credit_) - (d_4_debit_)
            result = (result).set(d_1_account_, (d_4_debit_, d_5_credit_, d_6_balance_))
            d_0_i_ = (d_0_i_) + (1)
        return result

