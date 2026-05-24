from typing import Dict, Set


def has_permission(matrix: dict[str, set[str]], role: str, permission: str) -> bool:
    """
    Return True when `permission` is granted either:
      - explicitly to `role`, or
      - via the wildcard role '*'.

    Deny by default when neither applies. Unknown roles or permissions must not raise.
    If no wildcard entry exists, behavior is the same as explicit-role-only lookup.
    """
    if not isinstance(matrix, dict):
        return False

    role_perms = matrix.get(role)
    if isinstance(role_perms, set) and permission in role_perms:
        return True

    wildcard_perms = matrix.get("*")
    if isinstance(wildcard_perms, set) and permission in wildcard_perms:
        return True

    return False