from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateBlueprint:
    suffix: str
    source: str
    label: str
    visible_tests_pass: bool
    hidden_tests_pass: bool
    property_checks_pass: bool
    regression_checks_pass: bool
    security_checks_pass: bool
    parse_ok: bool
    deceptive: bool
    insecure: bool
    regression: bool
    cc_average: float
    max_nesting_depth: int
    maintainability_index: float
    redundancy_score: float


BASE_BLUEPRINTS: tuple[CandidateBlueprint, ...] = (
    CandidateBlueprint("correct", "reference_oracle", "correct", True, True, True, True, True, True, False, False, False, 2.0, 1, 88.0, 0.03),
    CandidateBlueprint("visible_hidden_fail", "visible_pass_hidden_fail", "plausible_wrong", True, False, False, True, True, True, True, False, False, 2.4, 1, 86.0, 0.04),
    CandidateBlueprint("regression", "regression_revert", "regression_fail", True, False, True, False, True, True, True, False, True, 2.2, 1, 87.0, 0.02),
    CandidateBlueprint("runtime", "exception_swallowing", "runtime_fail", False, False, False, False, True, True, False, False, True, 4.5, 3, 70.0, 0.12),
    CandidateBlueprint("syntax", "syntax_break", "syntax_fail", False, False, False, False, False, False, False, False, False, 0.0, 0, 0.0, 0.0),
    CandidateBlueprint("structural_wrong", "structurally_neat_wrong", "plausible_wrong", True, False, True, True, True, True, True, False, False, 1.3, 1, 92.0, 0.01),
    CandidateBlueprint("bloat", "overfit_bloat", "plausible_wrong", True, False, True, True, True, True, True, False, False, 9.5, 5, 48.0, 0.31),
    CandidateBlueprint("unsafe", "unsafe_security", "security_fail", True, False, False, True, False, True, True, True, False, 2.6, 1, 82.0, 0.06),
)


def blueprints_for_surface(surface: str, minimum: int) -> list[CandidateBlueprint]:
    blueprints = list(BASE_BLUEPRINTS)
    if surface != "secure":
        blueprints = [bp for bp in blueprints if bp.suffix != "unsafe"] + [
            CandidateBlueprint("compact_correct", "structural_discipline", "correct", True, True, True, True, True, True, False, False, False, 1.4, 1, 91.0, 0.01)
        ]
    while len(blueprints) < minimum:
        idx = len(blueprints)
        blueprints.append(
            CandidateBlueprint(
                f"seed{idx}",
                "temperature_variant",
                "plausible_wrong" if idx % 2 else "correct",
                True,
                idx % 2 == 0,
                idx % 3 != 0,
                idx % 4 != 0,
                True,
                True,
                idx % 2 == 1,
                False,
                idx % 4 == 0,
                2.0 + (idx % 5),
                1 + (idx % 3),
                80.0 - idx,
                round((idx % 4) / 20, 3),
            )
        )
    return blueprints[:minimum]


def render_candidate_code(task_id: str, blueprint: CandidateBlueprint) -> str:
    if not blueprint.parse_ok:
        return f"def solution_{task_id.replace('-', '_')}(:\n    return None\n"
    safe_task = task_id.replace("-", "_").replace(":", "_")
    body = [
        f"def solution_{safe_task}(payload=None):",
        f"    \"\"\"Deterministic vericoding candidate: {blueprint.source}.\"\"\"",
    ]
    if blueprint.label == "correct":
        body.append("    return {'ok': True, 'payload': payload}")
    elif blueprint.label == "security_fail":
        body.append("    return {'ok': True, 'unsafe': True, 'payload': payload}")
    elif blueprint.label == "regression_fail":
        body.append("    return {'ok': True, 'regression': True}")
    elif blueprint.label == "runtime_fail":
        body.append("    raise RuntimeError('synthetic runtime failure')")
    else:
        body.append("    return {'ok': False, 'payload': payload}")
    return "\n".join(body) + "\n"
