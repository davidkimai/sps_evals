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
    def ParseCliArgs(argv):
        result: _dafny.Map = _dafny.Map({})
        d_0_input_: _dafny.Seq
        d_0_input_ = _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, ""))
        d_1_limit_: _dafny.Seq
        d_1_limit_ = _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "100"))
        d_2_format_: _dafny.Seq
        d_2_format_ = _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "json"))
        d_3_dry__run_: _dafny.Seq
        d_3_dry__run_ = _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "false"))
        d_4_hasInput_: bool
        d_4_hasInput_ = False
        d_5_i_: int
        d_5_i_ = 0
        while (d_5_i_) < (len(argv)):
            d_6_arg_: _dafny.Seq
            d_6_arg_ = (argv)[d_5_i_]
            if (d_6_arg_) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "--input"))):
                if ((d_5_i_) + (1)) >= (len(argv)):
                    d_5_i_ = (d_5_i_) + (1)
                elif True:
                    d_5_i_ = (d_5_i_) + (1)
                    d_0_input_ = (argv)[d_5_i_]
                    d_4_hasInput_ = True
                    d_5_i_ = (d_5_i_) + (1)
            elif (d_6_arg_) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "--limit"))):
                if ((d_5_i_) + (1)) >= (len(argv)):
                    d_5_i_ = (d_5_i_) + (1)
                elif True:
                    d_5_i_ = (d_5_i_) + (1)
                    d_1_limit_ = (argv)[d_5_i_]
                    d_5_i_ = (d_5_i_) + (1)
            elif (d_6_arg_) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "--format"))):
                if ((d_5_i_) + (1)) >= (len(argv)):
                    d_5_i_ = (d_5_i_) + (1)
                elif True:
                    d_5_i_ = (d_5_i_) + (1)
                    d_2_format_ = (argv)[d_5_i_]
                    d_5_i_ = (d_5_i_) + (1)
            elif (d_6_arg_) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "--dry-run"))):
                d_3_dry__run_ = _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "true"))
                d_5_i_ = (d_5_i_) + (1)
            elif True:
                d_5_i_ = (d_5_i_) + (1)
        result = _dafny.Map({_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "input")): d_0_input_, _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "limit")): d_1_limit_, _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "format")): d_2_format_, _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "dry_run")): d_3_dry__run_})
        return result

    @staticmethod
    def Main(noArgsParameter__):
        d_0_args_: _dafny.Seq
        d_0_args_ = _dafny.SeqWithoutIsStrInference([_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "--input")), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "file.txt")), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "--limit")), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "50")), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "--format")), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "csv")), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "--dry-run"))])
        d_1_r_: _dafny.Map
        out0_: _dafny.Map
        out0_ = default__.ParseCliArgs(d_0_args_)
        d_1_r_ = out0_
        _dafny.print(((d_1_r_)[_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "input"))]).VerbatimString(False))
        _dafny.print((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "\n"))).VerbatimString(False))
        _dafny.print(((d_1_r_)[_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "limit"))]).VerbatimString(False))
        _dafny.print((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "\n"))).VerbatimString(False))
        _dafny.print(((d_1_r_)[_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "format"))]).VerbatimString(False))
        _dafny.print((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "\n"))).VerbatimString(False))
        _dafny.print(((d_1_r_)[_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "dry_run"))]).VerbatimString(False))
        _dafny.print((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "\n"))).VerbatimString(False))

