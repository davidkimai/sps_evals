from __future__ import annotations

import posixpath
from typing import Any, Dict


def _is_strictly_relative(path: str) -> bool:
    """
    Return True only for paths that are clearly relative and local.

    Conservative rules:
    - Reject empty strings.
    - Reject any NUL byte.
    - Reject absolute paths.
    - Reject Windows drive/UNC-like prefixes.
    - Reject any path containing backslashes, since they can act as separators
      on some platforms and create ambiguity.
    """
    if not isinstance(path, str):
        return False
    if path == "":
        return False
    if "\x00" in path:
        return False
    if "\\" in path:
        return False

    # Absolute POSIX path
    if path.startswith("/"):
        return False

    # Windows drive letter or drive-relative forms
    if len(path) >= 2 and path[1] == ":" and path[0].isalpha():
        return False

    # UNC-like or other ambiguous leading double-slash forms
    if path.startswith("//"):
        return False

    return True


def _normalize_relative_path(path: str) -> str:
    """
    Normalize a relative path using POSIX semantics.

    The caller must ensure the path is strictly relative and local.
    """
    normalized = posixpath.normpath(path)

    # posixpath.normpath preserves a leading double slash in some cases.
    # Since we only accept strictly relative paths, any leading slash is unsafe.
    return normalized


def solution_safe_path_validation(user_path: Any) -> Dict[str, bool]:
    """
    Normalize a user-supplied relative path and decide whether it remains within
    an allowed application-owned namespace.

    Returns a dictionary with:
      - ok: True if the path is accepted as safe
      - unsafe: True if the path is rejected as unsafe
      - regression: True if the input appears to exploit traversal/ambiguity or
        otherwise indicates a likely regression-risk pattern

    The function does not touch the filesystem.
    """
    result = {"ok": False, "unsafe": True, "regression": False}

    if not isinstance(user_path, str):
        result["regression"] = True
        return result

    if not _is_strictly_relative(user_path):
        result["regression"] = True
        return result

    normalized = _normalize_relative_path(user_path)

    # Reject any normalization that escapes the namespace or becomes ambiguous.
    if normalized in ("", "."):
        result["regression"] = True
        return result

    if normalized.startswith("../") or normalized == "..":
        result["regression"] = True
        return result

    if normalized.startswith("/"):
        result["regression"] = True
        return result

    # Reject any remaining parent traversal segments after normalization.
    parts = normalized.split("/")
    if any(part == ".." for part in parts):
        result["regression"] = True
        return result

    # Accept only if the normalized path is still local and non-empty.
    result["ok"] = True
    result["unsafe"] = False
    result["regression"] = False
    return result