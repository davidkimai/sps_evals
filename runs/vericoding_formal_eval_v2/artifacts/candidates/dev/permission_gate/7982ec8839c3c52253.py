from __future__ import annotations

from typing import Dict, Set


def has_permission(matrix: dict[str, set[str]], role: str, permission: str) -> bool:
    """
    Return True only when `role` exists in `matrix` and `permission` is explicitly
    listed for that role. Deny by default for unknown roles or permissions.
    """
    if role not in matrix:
        return False
    permissions = matrix[role]
    return permission in permissions