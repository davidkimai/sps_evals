from __future__ import annotations


def has_permission(matrix: dict[str, set[str]], role: str, permission: str) -> bool:
    """Return whether a role is granted a permission.

    A permission is granted if it appears in the permission set for the given
    role, or in the permission set for the wildcard role "*". Missing roles,
    missing permissions, and a missing wildcard entry deny by default.
    """
    role_permissions = matrix.get(role)
    if role_permissions is not None and permission in role_permissions:
        return True

    wildcard_permissions = matrix.get("*")
    if wildcard_permissions is not None and permission in wildcard_permissions:
        return True

    return False


__all__ = ["has_permission"]