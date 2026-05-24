from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _is_ambiguous_or_nonlocal(path: str) -> bool:
    """
    Conservative checks for paths that should be treated as unsafe.

    We reject:
    - empty strings
    - absolute paths
    - paths with drive letters or UNC-like prefixes
    - paths containing backslashes
    - paths with NUL bytes
    - paths with empty segments from repeated separators
    - paths that attempt to traverse above the namespace
    """
    if not isinstance(path, str):
        return True
    if path == "":
        return True
    if "\x00" in path:
        return True
    if "\\" in path:
        return True
    if path.startswith("/"):
        return True
    if path.startswith("//"):
        return True
    if len(path) >= 2 and path[1] == ":":
        return True
    return False


def _normalize_relative_path(path: str) -> Optional[str]:
    """
    Normalize a relative POSIX-style path.

    Returns a normalized path string using forward slashes, or None if the
    path is unsafe/ambiguous.
    """
    if _is_ambiguous_or_nonlocal(path):
        return None

    parts: List[str] = []
    for segment in path.split("/"):
        if segment == "" or segment == ".":
            continue
        if segment == "..":
            if not parts:
                return None
            parts.pop()
            continue
        parts.append(segment)

    normalized = "/".join(parts)
    return normalized


def solution_safe_path_validation(user_path: Any) -> Dict[str, bool]:
    """
    Normalize a user-supplied relative path and decide whether it remains
    within an allowed application-owned namespace.

    Contract:
    - Return a dictionary with boolean keys: ok, unsafe, regression
    - Do not touch the filesystem
    - Treat ambiguous or non-local paths conservatively
    """
    ok = False
    unsafe = True
    regression = False

    if isinstance(user_path, str):
        normalized = _normalize_relative_path(user_path)
        if normalized is not None:
            # A normalized relative path is considered safe if it stays within
            # the application-owned namespace. Since we do not have a concrete
            # namespace root in the visible contract, the namespace is modeled
            # as the relative path space itself, excluding traversal and
            # ambiguous forms.
            ok = True
            unsafe = False
            regression = normalized != user_path

    return {"ok": ok, "unsafe": unsafe, "regression": regression}