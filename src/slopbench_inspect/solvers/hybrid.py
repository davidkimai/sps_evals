from __future__ import annotations

from typing import Any

from inspect_ai.model import ChatMessageUser
from inspect_ai.solver import Generate, Solver, TaskState, solver, system_message

from specoracle.config import BASELINE_SYSTEM_PROMPT
from specoracle.generator import extract_python_code
from specoracle.metrics import build_structural_metric_record


def hybrid_gate(
    code: str,
    *,
    max_cc: float = 8.0,
    max_nesting: int = 3,
) -> dict[str, Any]:
    metrics = build_structural_metric_record(code, language="python")
    parse_ok = bool(metrics.get("parse_ok"))
    cc_average = metrics.get("cc_average")
    nesting = metrics.get("max_nesting_depth")
    passed = (
        parse_ok
        and isinstance(cc_average, int | float)
        and float(cc_average) <= max_cc
        and isinstance(nesting, int | float)
        and int(nesting) <= max_nesting
    )
    reasons: list[str] = []
    if not parse_ok:
        reasons.append("parse_failed")
    if isinstance(cc_average, int | float) and float(cc_average) > max_cc:
        reasons.append("cc_gate_failed")
    if isinstance(nesting, int | float) and int(nesting) > max_nesting:
        reasons.append("nesting_gate_failed")
    return {
        "passed": passed,
        "reasons": reasons,
        "cc_average": cc_average,
        "max_nesting_depth": nesting,
        "parse_ok": parse_ok,
    }


@solver
def hybrid_solver(
    *,
    max_cc: float = 8.0,
    max_nesting: int = 3,
    max_retries: int = 3,
) -> Solver:
    """CEGIS-style structural gate/retry solver for Inspect."""
    system = system_message(BASELINE_SYSTEM_PROMPT)

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        state = await system(state, generate)
        retries = 0
        gate: dict[str, Any] = {"passed": False, "reasons": ["not_run"]}
        while True:
            state = await generate(state)
            code = extract_python_code(state.output.completion if state.output else "")
            gate = hybrid_gate(code, max_cc=max_cc, max_nesting=max_nesting)
            if gate["passed"] or retries >= max_retries:
                break
            retries += 1
            state.messages.append(
                ChatMessageUser(
                    content=(
                        "Revise the complete Python module. Keep the same behavior, "
                        "but reduce structural complexity. Gate failures: "
                        f"{', '.join(gate['reasons']) or 'unknown'}."
                    )
                )
            )
        state.store.set("solver_variant", "hybrid")
        state.store.set("hybrid_retries", retries)
        state.store.set("hybrid_gate", gate)
        return state

    return solve
