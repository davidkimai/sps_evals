import sys
from typing import Callable, Any, TypeVar, NamedTuple
from math import floor
from itertools import count

import module_ as module_
import _dafny as _dafny
import System_ as System_

# Module: module_


class TokenBucketEnforcer:
    def  __init__(self):
        self.capacity: int = int(0)
        self.tokens: int = int(0)
        pass

    def __dafnystr__(self) -> str:
        return "_module.TokenBucketEnforcer"
    def ctor__(self, capacity, refill__rate):
        (self).capacity = capacity
        (self).tokens = capacity

    def allow(self, cost):
        result: bool = False
        if (cost) <= (self.tokens):
            (self).tokens = (self.tokens) - (cost)
            result = True
        elif True:
            result = False
        return result

    def refill(self, amount):
        d_0_newTokens_: int
        d_0_newTokens_ = (self.tokens) + (amount)
        if (d_0_newTokens_) > (self.capacity):
            (self).tokens = self.capacity
        elif True:
            (self).tokens = d_0_newTokens_

