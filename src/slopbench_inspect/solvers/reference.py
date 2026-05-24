from __future__ import annotations

from inspect_ai.model import ModelOutput
from inspect_ai.solver import Generate, Solver, TaskState, solver


@solver
def reference_solution_solver() -> Solver:
    """Deterministic no-provider solver used for runtime smoke tests."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        code = ""
        if state.metadata:
            code = str(state.metadata.get("mock_solution") or state.metadata.get("human_reference") or "")
        state.output = ModelOutput.from_content(model="reference-solver", content=code)
        state.store.set("solver_variant", "reference")
        return state

    return solve
