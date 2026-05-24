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
    def SplitByComma(line):
        parts: _dafny.Seq = _dafny.Seq({})
        d_0_result_: _dafny.Seq
        d_0_result_ = _dafny.SeqWithoutIsStrInference([])
        d_1_current_: _dafny.Seq
        d_1_current_ = _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, ""))
        d_2_i_: int
        d_2_i_ = 0
        while (d_2_i_) < (len(line)):
            if ((line)[d_2_i_]) == (_dafny.CodePoint(',')):
                d_0_result_ = (d_0_result_) + (_dafny.SeqWithoutIsStrInference([d_1_current_]))
                d_1_current_ = _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, ""))
            elif True:
                d_1_current_ = (d_1_current_) + (_dafny.SeqWithoutIsStrInference([(line)[d_2_i_]]))
            d_2_i_ = (d_2_i_) + (1)
        d_0_result_ = (d_0_result_) + (_dafny.SeqWithoutIsStrInference([d_1_current_]))
        parts = d_0_result_
        return parts

    @staticmethod
    def ParseCSVRows(lines):
        rows: _dafny.Seq = _dafny.Seq({})
        rows = _dafny.SeqWithoutIsStrInference([])
        d_0_headers_: _dafny.Seq
        d_0_headers_ = _dafny.SeqWithoutIsStrInference([])
        d_1_headerFound_: bool
        d_1_headerFound_ = False
        d_2_i_: int
        d_2_i_ = 0
        while (d_2_i_) < (len(lines)):
            d_3_line_: _dafny.Seq
            d_3_line_ = (lines)[d_2_i_]
            if (len(d_3_line_)) > (0):
                if not(d_1_headerFound_):
                    out0_: _dafny.Seq
                    out0_ = default__.SplitByComma(d_3_line_)
                    d_0_headers_ = out0_
                    d_1_headerFound_ = True
                elif True:
                    d_4_cells_: _dafny.Seq
                    out1_: _dafny.Seq
                    out1_ = default__.SplitByComma(d_3_line_)
                    d_4_cells_ = out1_
                    d_5_row_: _dafny.Map
                    d_5_row_ = _dafny.Map({})
                    d_6_j_: int
                    d_6_j_ = 0
                    d_7_limit_: int
                    if (len(d_0_headers_)) < (len(d_4_cells_)):
                        d_7_limit_ = len(d_0_headers_)
                    elif True:
                        d_7_limit_ = len(d_4_cells_)
                    while (d_6_j_) < (d_7_limit_):
                        d_5_row_ = (d_5_row_).set((d_0_headers_)[d_6_j_], (d_4_cells_)[d_6_j_])
                        d_6_j_ = (d_6_j_) + (1)
                    while (d_6_j_) < (len(d_0_headers_)):
                        d_5_row_ = (d_5_row_).set((d_0_headers_)[d_6_j_], _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "")))
                        d_6_j_ = (d_6_j_) + (1)
                    rows = (rows) + (_dafny.SeqWithoutIsStrInference([d_5_row_]))
            d_2_i_ = (d_2_i_) + (1)
        return rows

    @staticmethod
    def Main(noArgsParameter__):
        d_0_lines_: _dafny.Seq
        d_0_lines_ = _dafny.SeqWithoutIsStrInference([_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "name,age,city")), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "Alice,30,NYC")), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "Bob,25,LA")), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "")), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "Carol,35,Chicago"))])
        d_1_rows_: _dafny.Seq
        out0_: _dafny.Seq
        out0_ = default__.ParseCSVRows(d_0_lines_)
        d_1_rows_ = out0_
        d_2_i_: int
        d_2_i_ = 0
        while (d_2_i_) < (len(d_1_rows_)):
            _dafny.print(_dafny.string_of((d_1_rows_)[d_2_i_]))
            _dafny.print((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "\n"))).VerbatimString(False))
            d_2_i_ = (d_2_i_) + (1)

