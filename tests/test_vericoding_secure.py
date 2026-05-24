from __future__ import annotations

from specoracle.vericoding.security_checks import SECURE_TASKS, hidden_oracle_hash


def test_secure_subset_contains_required_families_and_hashes_only() -> None:
    categories = {task.category for task in SECURE_TASKS}
    assert "path_validation" in categories
    assert "shell_args" in categories
    assert "authorization" in categories
    digest = hidden_oracle_hash("safe_path_validation")
    assert len(digest) == 64
