from __future__ import annotations


def has_permission(matrix: dict[str, set[str]], role: str, permission: str) -> bool:
    return permission in matrix.get(role, set())
