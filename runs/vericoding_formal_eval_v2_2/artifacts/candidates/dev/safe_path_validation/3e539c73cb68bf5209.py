from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any, Dict


def solution_safe_path_validation(path: Any) -> Dict[str, bool]:
    """
    Normalize a user-supplied relative path and decide whether it remains within
    an allowed application-owned namespace.

    Contract:
      - Return a dictionary with boolean keys: ok, unsafe, regression.
      - Do not touch the filesystem.
      - Treat ambiguous or non-local paths conservatively.

    Interpretation:
      - "ok" means the path is a clearly local relative path that does not escape
        its namespace after normalization.
      - "unsafe" means the input is clearly dangerous or non-local.
      - "regression" flags inputs that are syntactically odd/ambiguous enough that
        a conservative caller should treat them as suspicious, even if they do not
        obviously escape.

    This function is intentionally strict.
    """
    result = {"ok": False, "unsafe": True, "regression": False}

    if not isinstance(path, str):
        result["regression"] = True
        return result

    if path == "":
        result["regression"] = True
        return result

    # Reject NUL and other control characters conservatively.
    if any(ord(ch) < 32 for ch in path):
        result["regression"] = True
        return result

    # Backslashes are ambiguous across platforms and can be used to smuggle
    # path separators on Windows-like systems. Treat them as unsafe.
    if "\\" in path:
        result["regression"] = True
        return result

    # Absolute or rooted paths are not allowed.
    if path.startswith("/"):
        return result

    # Reject drive-like or URI-like prefixes conservatively.
    lowered = path.lower()
    if len(path) >= 2 and path[1] == ":":
        result["regression"] = True
        return result
    if lowered.startswith("file:") or lowered.startswith("http:") or lowered.startswith("https:"):
        result["regression"] = True
        return result

    # Normalize using POSIX semantics only; we are validating a relative namespace.
    p = PurePosixPath(path)

    # PurePosixPath preserves leading ".." segments; any attempt to escape the
    # namespace is unsafe.
    if p.is_absolute():
        return result

    parts = p.parts

    # Empty or dot-only paths are not useful and are treated conservatively.
    if not parts or parts == (".",):
        result["regression"] = True
        return result

    normalized_parts = []
    for part in parts:
        if part == ".":
            result["regression"] = True
            continue
        if part == "..":
            # Any parent traversal is considered an escape attempt.
            return result
        if part == "":
            result["regression"] = True
            continue
        normalized_parts.append(part)

    if not normalized_parts:
        result["regression"] = True
        return result

    # Reject hidden ambiguity patterns that can be surprising in application-owned
    # namespaces.
    for part in normalized_parts:
        if part in {".", ".."}:
            result["regression"] = True
            return result
        if "\x00" in part:
            result["regression"] = True
            return result

    result["ok"] = True
    result["unsafe"] = False
    return result