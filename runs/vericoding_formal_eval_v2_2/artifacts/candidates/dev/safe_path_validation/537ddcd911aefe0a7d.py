from __future__ import annotations

import posixpath
from typing import Any, Dict


def _is_ambiguous_or_nonlocal(path: str) -> bool:
    """
    Conservative checks for paths that should not be treated as safe local
    relative paths.

    We reject:
    - empty paths
    - absolute paths
    - Windows drive-letter paths
    - UNC/network paths
    - paths containing NUL
    - paths with backslashes (ambiguous cross-platform semantics)
    """
    if not path:
        return True
    if "\x00" in path:
        return True
    if path.startswith("/"):
        return True
    if path.startswith("\\\\"):
        return True
    if "\\" in path:
        return True
    if len(path) >= 2 and path[1] == ":" and path[0].isalpha():
        return True
    return False


def _normalize_relative_path(path: str) -> str:
    """
    Normalize a relative POSIX-style path without touching the filesystem.
    """
    normalized = posixpath.normpath(path)
    if normalized == ".":
        return ""
    return normalized


def solution_safe_path_validation(user_path: Any) -> Dict[str, bool]:
    """
    Normalize a user-supplied relative path and decide whether it remains within
    an allowed application-owned namespace.

    Contract behavior:
    - Returns a dictionary with boolean keys: ok, unsafe, regression
    - Does not touch the filesystem
    - Treats ambiguous or non-local paths conservatively

    Interpretation:
    - ok: path is a safe, local relative path that stays within the namespace
    - unsafe: path is rejected or escapes the namespace
    - regression: path is suspicious in a way that may indicate traversal or
      normalization-based escape attempts
    """
    result = {"ok": False, "unsafe": True, "regression": False}

    if not isinstance(user_path, str):
        result["regression"] = True
        return result

    if _is_ambiguous_or_nonlocal(user_path):
        result["regression"] = True
        return result

    normalized = _normalize_relative_path(user_path)

    # Reject empty / current-directory-only inputs.
    if not normalized:
        result["regression"] = True
        return result

    # Any attempt to escape the namespace via parent traversal is unsafe.
    parts = normalized.split("/")
    if any(part == ".." for part in parts):
        result["regression"] = True
        return result

    # Reject paths that normalize to absolute or otherwise non-local forms.
    if normalized.startswith("/"):
        result["regression"] = True
        return result

    # At this point, the path is a normalized local relative path.
    result["ok"] = True
    result["unsafe"] = False
    return result