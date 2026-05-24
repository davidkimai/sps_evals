from __future__ import annotations

import posixpath
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _to_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return str(value)


def _split_components(path: str) -> List[str]:
    parts = []
    for part in path.split("/"):
        if part == "" or part == ".":
            continue
        parts.append(part)
    return parts


def _normalize_relative_path(path: str) -> Tuple[Optional[str], bool, bool]:
    """
    Normalize a user-supplied relative path.

    Returns:
        (normalized_path_or_none, unsafe, regression)

    normalized_path_or_none is a POSIX-style relative path without leading slash,
    or None if the path is ambiguous/non-local/unsafe.
    """
    raw = _to_text(path).strip()

    if raw == "":
        return "", False, False

    # Reject obvious non-local or ambiguous forms conservatively.
    if "\x00" in raw:
        return None, True, False
    if raw.startswith("/") or raw.startswith("\\"):
        return None, True, False
    if ":" in raw:
        # Conservative: reject drive letters, URI-like forms, and other colon-bearing inputs.
        return None, True, False

    # Normalize separators to POSIX style.
    raw = raw.replace("\\", "/")

    # Collapse repeated separators and dot segments.
    parts = _split_components(raw)
    stack: List[str] = []
    regression = False

    for part in parts:
        if part == "..":
            if stack:
                stack.pop()
                regression = True
            else:
                # Would escape the allowed namespace.
                return None, True, regression
        else:
            stack.append(part)

    normalized = "/".join(stack)
    return normalized, False, regression


def solution_safe_path_validation(user_path: Any) -> Dict[str, Any]:
    """
    Normalize a user-supplied relative path and decide whether it remains within
    an allowed application-owned namespace.

    Contract:
        - Return a dictionary with boolean ok, unsafe, and regression fields.
        - Do not touch the filesystem.
        - Treat ambiguous or non-local paths conservatively.
    """
    normalized, unsafe, regression = _normalize_relative_path(user_path)

    ok = not unsafe

    result: Dict[str, Any] = {
        "ok": bool(ok),
        "unsafe": bool(unsafe),
        "regression": bool(regression),
    }

    # Preserve useful normalized output without changing the required fields.
    if normalized is not None:
        result["normalized"] = normalized

    return result