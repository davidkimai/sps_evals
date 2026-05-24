def has_permission(matrix: dict[str, set[str]], role: str, permission: str) -> bool:
    """Return True only when the role exists and explicitly lists the permission."""
    if role not in matrix:
        return False
    return permission in matrix[role]