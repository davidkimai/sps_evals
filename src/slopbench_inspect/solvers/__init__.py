"""Inspect solver conditions for SlopBench basins."""

from slopbench_inspect.solvers.baseline import baseline_solver
from slopbench_inspect.solvers.hybrid import hybrid_gate, hybrid_solver
from slopbench_inspect.solvers.karpathy import karpathy_solver
from slopbench_inspect.solvers.reference import reference_solution_solver

__all__ = [
    "baseline_solver",
    "hybrid_gate",
    "hybrid_solver",
    "karpathy_solver",
    "reference_solution_solver",
]
