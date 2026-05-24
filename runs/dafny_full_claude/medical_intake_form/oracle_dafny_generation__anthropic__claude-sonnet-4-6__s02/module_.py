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
    def validate__intake(patient__id, age, symptoms):
        result: tuple = (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "")), int(0), _dafny.Seq({}))
        result = (patient__id, age, symptoms)
        return result

    @staticmethod
    def Main(noArgsParameter__):
        d_0_r_: tuple
        out0_: tuple
        out0_ = default__.validate__intake(_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "P001")), 30, _dafny.SeqWithoutIsStrInference([_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "fever")), _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "cough"))]))
        d_0_r_ = out0_
        _dafny.print((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "patient_id: "))).VerbatimString(False))
        _dafny.print(((d_0_r_)[0]).VerbatimString(False))
        _dafny.print((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "\n"))).VerbatimString(False))
        _dafny.print((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "age: "))).VerbatimString(False))
        _dafny.print(_dafny.string_of((d_0_r_)[1]))
        _dafny.print((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "\n"))).VerbatimString(False))
        _dafny.print((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "symptoms: "))).VerbatimString(False))
        _dafny.print(_dafny.string_of((d_0_r_)[2]))
        _dafny.print((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "\n"))).VerbatimString(False))

