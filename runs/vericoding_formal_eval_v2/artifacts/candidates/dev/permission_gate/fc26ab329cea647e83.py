from __future__ import annotations

from typing import Dict, Set


def has_permission(matrix: dict[str, set[str]], role: str, permission: str) -> bool:
    """
    Return True only when:
    - role exists in matrix
    - permission is explicitly listed in that role's permission set

    Deny by default for unknown roles or permissions.
    """
    permissions = matrix.get(role)
    if permissions is None:
        return False
    return permission in permissions