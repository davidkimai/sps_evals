"""Inspect task entrypoints."""

from slopbench_inspect.tasks.internal import slopbench_internal_smoke
from slopbench_inspect.tasks.scbench_longitudinal import scbench_external_subset
from slopbench_inspect.tasks.terminalbench_python_slice import terminalbench_python_slice
from slopbench_inspect.tasks.vericoding_bank_construction import vericoding_bank_construction
from slopbench_inspect.tasks.vericoding_candidate_bank import vericoding_candidate_bank
from slopbench_inspect.tasks.vericoding_e2e import vericoding_e2e
from slopbench_inspect.tasks.vericoding_external_guardrail import vericoding_external_guardrail
from slopbench_inspect.tasks.vericoding_fixed_bank_selector import vericoding_fixed_bank_selector
from slopbench_inspect.tasks.vericoding_formal_overlay import vericoding_formal_overlay
from slopbench_inspect.tasks.vericoding_internal_basins import vericoding_internal_basins
from slopbench_inspect.tasks.vericoding_primary_core import vericoding_primary_core
from slopbench_inspect.tasks.vericoding_scbench_transfer import vericoding_scbench_transfer
from slopbench_inspect.tasks.vericoding_secure_challenge import vericoding_secure_challenge
from slopbench_inspect.tasks.vericoding_secure_subset import vericoding_secure_subset
from slopbench_inspect.tasks.vericoding_selector_eval import vericoding_selector_eval
from slopbench_inspect.tasks.vericoding_trust_boundary_review import vericoding_trust_boundary_review
from slopbench_inspect.tasks.vericoding_triage_eval import vericoding_triage_eval

__all__ = [
    "slopbench_internal_smoke",
    "scbench_external_subset",
    "terminalbench_python_slice",
    "vericoding_bank_construction",
    "vericoding_candidate_bank",
    "vericoding_e2e",
    "vericoding_external_guardrail",
    "vericoding_fixed_bank_selector",
    "vericoding_formal_overlay",
    "vericoding_internal_basins",
    "vericoding_primary_core",
    "vericoding_scbench_transfer",
    "vericoding_secure_challenge",
    "vericoding_secure_subset",
    "vericoding_selector_eval",
    "vericoding_trust_boundary_review",
    "vericoding_triage_eval",
]
