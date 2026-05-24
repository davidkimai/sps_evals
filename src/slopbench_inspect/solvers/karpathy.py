from __future__ import annotations

from inspect_ai.solver import Solver, generate, system_message

from specoracle.config import KARPATHY_ORACLE_SYSTEM_PROMPT


def karpathy_solver() -> list[Solver]:
    return [system_message(KARPATHY_ORACLE_SYSTEM_PROMPT), generate()]
