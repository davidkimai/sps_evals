from __future__ import annotations

from inspect_ai.solver import Solver, generate, system_message

from specoracle.config import BASELINE_SYSTEM_PROMPT


def baseline_solver() -> list[Solver]:
    return [system_message(BASELINE_SYSTEM_PROMPT), generate()]
