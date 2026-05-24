"""Inspect-native task surface for SpecOracle/SlopBench.

This package is intentionally narrow: it adds a local Inspect execution path
without replacing the legacy ``specoracle`` CLI or historical evidence.
"""

from __future__ import annotations

try:
    from slopbench_inspect.tasks.internal import slopbench_internal_smoke
    from slopbench_inspect.tasks.scbench_longitudinal import scbench_external_subset
    from slopbench_inspect.tasks.terminalbench_python_slice import terminalbench_python_slice
    from slopbench_inspect.tasks.vericoding_candidate_bank import vericoding_candidate_bank
    from slopbench_inspect.tasks.vericoding_e2e import vericoding_e2e
    from slopbench_inspect.tasks.vericoding_external_guardrail import vericoding_external_guardrail
    from slopbench_inspect.tasks.vericoding_formal_overlay import vericoding_formal_overlay
    from slopbench_inspect.tasks.vericoding_internal_basins import vericoding_internal_basins
    from slopbench_inspect.tasks.vericoding_primary_core import vericoding_primary_core
    from slopbench_inspect.tasks.vericoding_scbench_transfer import vericoding_scbench_transfer
    from slopbench_inspect.tasks.vericoding_secure_challenge import vericoding_secure_challenge
    from slopbench_inspect.tasks.vericoding_secure_subset import vericoding_secure_subset
    from slopbench_inspect.tasks.vericoding_selector_eval import vericoding_selector_eval
    from slopbench_inspect.tasks.vericoding_trust_boundary_review import vericoding_trust_boundary_review
except Exception:
    # Inspect entrypoint loading imports this package in many environments. Keep
    # import failure local to task resolution so normal package metadata remains
    # inspectable even when optional runtime dependencies are not installed.
    slopbench_internal_smoke = None  # type: ignore[assignment]
    scbench_external_subset = None  # type: ignore[assignment]
    terminalbench_python_slice = None  # type: ignore[assignment]
    vericoding_candidate_bank = None  # type: ignore[assignment]
    vericoding_e2e = None  # type: ignore[assignment]
    vericoding_external_guardrail = None  # type: ignore[assignment]
    vericoding_formal_overlay = None  # type: ignore[assignment]
    vericoding_internal_basins = None  # type: ignore[assignment]
    vericoding_primary_core = None  # type: ignore[assignment]
    vericoding_scbench_transfer = None  # type: ignore[assignment]
    vericoding_secure_challenge = None  # type: ignore[assignment]
    vericoding_secure_subset = None  # type: ignore[assignment]
    vericoding_selector_eval = None  # type: ignore[assignment]
    vericoding_trust_boundary_review = None  # type: ignore[assignment]

__all__ = [
    "slopbench_internal_smoke",
    "scbench_external_subset",
    "terminalbench_python_slice",
    "vericoding_candidate_bank",
    "vericoding_e2e",
    "vericoding_external_guardrail",
    "vericoding_formal_overlay",
    "vericoding_internal_basins",
    "vericoding_primary_core",
    "vericoding_scbench_transfer",
    "vericoding_secure_challenge",
    "vericoding_secure_subset",
    "vericoding_selector_eval",
    "vericoding_trust_boundary_review",
]
