from __future__ import annotations

import posixpath
from typing import Any, Dict


def solution_safe_path_validation(path: Any) -> Dict[str, bool]:
    """
    Normalize a user-supplied relative path and decide whether it remains within
    an allowed application-owned namespace.

    Contract:
      - Return a dictionary with boolean keys: ok, unsafe, regression.
      - Do not touch the filesystem.
      - Treat ambiguous or non-local paths conservatively.
    """
    result = {"ok": False, "unsafe": True, "regression": False}

    if not isinstance(path, str):
        return result

    if path == "":
        return result

    # Conservative rejection of ambiguous / non-local forms.
    # We only accept clearly relative POSIX-style paths.
    if path.startswith("/") or path.startswith("\\"):
        return result
    if path.startswith("~"):
        return result
    if ":" in path:
        return result
    if "\x00" in path:
        return result

    # Normalize using POSIX semantics without filesystem access.
    normalized = posixpath.normpath(path)

    # Reject empty, current-directory-only, or parent-traversal results.
    if normalized in ("", ".", ".."):
        return result

    # Reject any path that escapes upward or remains ambiguous after normalization.
    parts = normalized.split("/")
    if any(part == ".." for part in parts):
        return result

    # Reject paths that are still not clearly local after normalization.
    if normalized.startswith("/") or normalized.startswith("\\"):
        return result
    if normalized.startswith("~"):
        return result
    if ":" in normalized:
        return result

    # At this point, the path is a normalized relative path with no traversal.
    result["ok"] = True
    result["unsafe"] = False
    result["regression"] = False
    return result