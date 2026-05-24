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
                    d_7_val_: _dafny.Seq
                    d_7_val_ = (argv)[d_5_i_]
                    if (((len(d_7_val_)) >= (2)) and (((d_7_val_)[0]) == (_dafny.CodePoint('-')))) and (((d_7_val_)[1]) == (_dafny.CodePoint('-'))):
                        d_4_hasInput_ = False
                    elif True:
                        d_0_input_ = d_7_val_
                        d_4_hasInput_ = True
                        d_5_i_ = (d_5_i_) + (1)
            elif (d_6_arg_) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "--limit"))):
                if ((d_5_i_) + (1)) >= (len(argv)):
                    d_1_limit_ = _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, ""))
                    d_5_i_ = (d_5_i_) + (1)
                elif True:
                    d_5_i_ = (d_5_i_) + (1)
                    d_8_val_: _dafny.Seq
                    d_8_val_ = (argv)[d_5_i_]
                    if (((len(d_8_val_)) >= (2)) and (((d_8_val_)[0]) == (_dafny.CodePoint('-')))) and (((d_8_val_)[1]) == (_dafny.CodePoint('-'))):
                        d_1_limit_ = _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, ""))
                    elif True:
                        d_1_limit_ = d_8_val_
                        d_5_i_ = (d_5_i_) + (1)
            elif (d_6_arg_) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "--format"))):
                if ((d_5_i_) + (1)) >= (len(argv)):
                    d_2_format_ = _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, ""))
                    d_5_i_ = (d_5_i_) + (1)
                elif True:
                    d_5_i_ = (d_5_i_) + (1)
                    d_9_val_: _dafny.Seq
                    d_9_val_ = (argv)[d_5_i_]
                    if (((len(d_9_val_)) >= (2)) and (((d_9_val_)[0]) == (_dafny.CodePoint('-')))) and (((d_9_val_)[1]) == (_dafny.CodePoint('-'))):
                        d_2_format_ = _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, ""))
                    elif True:
                        d_2_format_ = d_9_val_
                        d_5_i_ = (d_5_i_) + (1)
            elif (d_6_arg_) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "--dry-run"))):
                d_3_dry__run_ = _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "true"))
                d_5_i_ = (d_5_i_) + (1)
            elif True:
                result = _dafny.Map({_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "input")): _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "")), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "limit")): _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "")), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "format")): _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "")), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "dry_run")): (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "error_unknown:"))) + (d_6_arg_)})
                return result
        if not(d_4_hasInput_):
            result = _dafny.Map({_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "input")): _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "")), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "limit")): _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "")), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "format")): _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "")), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "dry_run")): _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "error_missing_input"))})
            return result
        result = _dafny.Map({_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "input")): d_0_input_, _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "limit")): d_1_limit_, _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "format")): d_2_format_, _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "dry_run")): d_3_dry__run_})
        return result

    @staticmethod
    def Main(noArgsParameter__):
        d_0_argv1_: _dafny.Seq
        d_0_argv1_ = _dafny.SeqWithoutIsStrInference([_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "--input")), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "file.txt"))])
        d_1_r1_: _dafny.Map
        out0_: _dafny.Map
        out0_ = default__.ParseCliArgs(d_0_argv1_)
        d_1_r1_ = out0_
        _dafny.print(((d_1_r1_)[_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "input"))]).VerbatimString(False))
        _dafny.print((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "\n"))).VerbatimString(False))
        _dafny.print(((d_1_r1_)[_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "limit"))]).VerbatimString(False))
        _dafny.print((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "\n"))).VerbatimString(False))
        _dafny.print(((d_1_r1_)[_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "format"))]).VerbatimString(False))
        _dafny.print((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "\n"))).VerbatimString(False))
        _dafny.print(((d_1_r1_)[_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "dry_run"))]).VerbatimString(False))
        _dafny.print((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "\n"))).VerbatimString(False))

