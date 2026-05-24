from typing import Dict, Set


def has_permission(matrix: dict[str, set[str]], role: str, permission: str) -> bool:
    if role not in matrix:
        return False
    return permission in matrix[role]