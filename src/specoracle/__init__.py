"""SpecOracle: informal specifications as in-context synthesis oracles."""

from specoracle.config import GenerationMode, ModelSettings, Provider, Task
from specoracle.evaluator import EvaluationResult, StaticMetrics
from specoracle.generator import GenerationResult, SpecOracleGenerator
from specoracle.stress import SpecArena, StressResult

__all__ = [
    "EvaluationResult",
    "GenerationMode",
    "GenerationResult",
    "ModelSettings",
    "Provider",
    "SpecArena",
    "SpecOracleGenerator",
    "StaticMetrics",
    "StressResult",
    "Task",
]
