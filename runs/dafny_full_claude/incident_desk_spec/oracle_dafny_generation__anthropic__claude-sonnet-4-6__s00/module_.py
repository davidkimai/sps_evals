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
    def route__tickets(tickets, rules):
        result: _dafny.Seq = _dafny.Seq({})
        result = _dafny.SeqWithoutIsStrInference([])
        d_0_i_: int
        d_0_i_ = 0
        while (d_0_i_) < (len(tickets)):
            d_1_ticket_: _dafny.Map
            d_1_ticket_ = (tickets)[d_0_i_]
            if (((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "id"))) in (d_1_ticket_)) and ((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "severity"))) in (d_1_ticket_))) and ((_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "service"))) in (d_1_ticket_)):
                d_2_id_: _dafny.Seq
                d_2_id_ = (d_1_ticket_)[_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "id"))]
                d_3_severity_: _dafny.Seq
                d_3_severity_ = (d_1_ticket_)[_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "severity"))]
                d_4_service_: _dafny.Seq
                d_4_service_ = (d_1_ticket_)[_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "service"))]
                d_5_rule__key_: _dafny.Seq = _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, ""))
                if (d_4_service_) in (rules):
                    d_5_rule__key_ = d_4_service_
                elif True:
                    d_5_rule__key_ = _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "default"))
                d_6_rule_: _dafny.Map
                d_6_rule_ = (rules)[d_5_rule__key_]
                d_7_queue_: _dafny.Seq
                d_7_queue_ = (d_6_rule_)[_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "queue"))]
                d_8_base__priority__str_: _dafny.Seq
                d_8_base__priority__str_ = (d_6_rule_)[_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "priority"))]
                d_9_base__priority_: int
                d_9_base__priority_ = default__.parse__int(d_8_base__priority__str_)
                d_10_bonus_: int
                d_10_bonus_ = 0
                if (d_3_severity_) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "critical"))):
                    d_10_bonus_ = 10
                elif (d_3_severity_) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "high"))):
                    d_10_bonus_ = 5
                d_11_final__priority_: int
                d_11_final__priority_ = (d_9_base__priority_) + (d_10_bonus_)
                d_12_priority__str_: _dafny.Seq
                d_12_priority__str_ = default__.int__to__string(d_11_final__priority_)
                d_13_row_: _dafny.Map
                d_13_row_ = _dafny.Map({_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "id")): d_2_id_, _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "queue")): d_7_queue_, _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "priority")): d_12_priority__str_, _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "status_code")): _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "routed"))})
                result = (result) + (_dafny.SeqWithoutIsStrInference([d_13_row_]))
            d_0_i_ = (d_0_i_) + (1)
        return result

    @staticmethod
    def parse__int(s):
        if (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, ""))):
            return 0
        elif (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "0"))):
            return 0
        elif (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "1"))):
            return 1
        elif (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "2"))):
            return 2
        elif (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "3"))):
            return 3
        elif (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "4"))):
            return 4
        elif (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "5"))):
            return 5
        elif (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "6"))):
            return 6
        elif (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "7"))):
            return 7
        elif (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "8"))):
            return 8
        elif (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "9"))):
            return 9
        elif (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "10"))):
            return 10
        elif (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "11"))):
            return 11
        elif (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "12"))):
            return 12
        elif (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "13"))):
            return 13
        elif (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "14"))):
            return 14
        elif (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "15"))):
            return 15
        elif (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "16"))):
            return 16
        elif (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "17"))):
            return 17
        elif (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "18"))):
            return 18
        elif (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "19"))):
            return 19
        elif (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "20"))):
            return 20
        elif (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "25"))):
            return 25
        elif (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "30"))):
            return 30
        elif (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "50"))):
            return 50
        elif (s) == (_dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "100"))):
            return 100
        elif True:
            return 0

    @staticmethod
    def int__to__string(n):
        if (n) == (0):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "0"))
        elif (n) == (1):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "1"))
        elif (n) == (2):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "2"))
        elif (n) == (3):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "3"))
        elif (n) == (4):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "4"))
        elif (n) == (5):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "5"))
        elif (n) == (6):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "6"))
        elif (n) == (7):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "7"))
        elif (n) == (8):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "8"))
        elif (n) == (9):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "9"))
        elif (n) == (10):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "10"))
        elif (n) == (11):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "11"))
        elif (n) == (12):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "12"))
        elif (n) == (13):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "13"))
        elif (n) == (14):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "14"))
        elif (n) == (15):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "15"))
        elif (n) == (16):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "16"))
        elif (n) == (17):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "17"))
        elif (n) == (18):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "18"))
        elif (n) == (19):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "19"))
        elif (n) == (20):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "20"))
        elif (n) == (21):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "21"))
        elif (n) == (22):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "22"))
        elif (n) == (23):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "23"))
        elif (n) == (24):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "24"))
        elif (n) == (25):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "25"))
        elif (n) == (26):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "26"))
        elif (n) == (27):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "27"))
        elif (n) == (28):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "28"))
        elif (n) == (29):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "29"))
        elif (n) == (30):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "30"))
        elif (n) == (35):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "35"))
        elif (n) == (40):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "40"))
        elif (n) == (50):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "50"))
        elif (n) == (55):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "55"))
        elif (n) == (60):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "60"))
        elif (n) == (100):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "100"))
        elif (n) == (105):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "105"))
        elif (n) == (110):
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "110"))
        elif True:
            return _dafny.SeqWithoutIsStrInference(map(_dafny.CodePoint, "unknown"))

