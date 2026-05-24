from __future__ import annotations

from inspect_ai.model import ModelOutput
from inspect_ai.solver import Generate, Solver, TaskState, solver


@solver
def vericoding_runtime_provenance_solver(phase: str) -> Solver:
    """Minimal solver for manifest-driven vericoding runtime provenance tasks.

    Claim-bearing code generation, selection, and triage are orchestrated by the
    research runner and written to canonical ledgers. This solver keeps Inspect
    logs as the runtime provenance layer without injecting reference solutions.
    """

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        task_id = ""
        if state.metadata:
            task_id = str(state.metadata.get("task_id") or state.sample_id or "")
        state.output = ModelOutput.from_content(
            model=f"vericoding-runtime/{phase}",
            content=f"ledger-backed vericoding phase={phase} task_id={task_id}",
        )
        state.store.set("solver_variant", f"vericoding_runtime_provenance:{phase}")
        return state

    return solve
