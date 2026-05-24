"""Permission gate module.

Visible invariants and precedence rules:
1. Access is granted only by an explicit permission listing.
2. The role must exist in the permission matrix.
3. The requested permission must be a member of that role's permission set.
4. Unknown roles are denied by default.
5. Unknown or unlisted permissions are denied by default.
"""


def has_permission(matrix: dict[str, set[str]], role: str, permission: str) -> bool:
    """Return True only if role exists and permission is explicitly listed."""
    if role not in matrix:
        return False

    permissions_for_role = matrix[role]
    if permission not in permissions_for_role:
        return False

    return True