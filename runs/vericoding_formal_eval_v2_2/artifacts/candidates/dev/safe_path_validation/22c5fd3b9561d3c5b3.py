from __future__ import annotations

from typing import Any, Dict


def _is_safe_relative_path(path: str) -> bool:
    if path == "":
        return False

    # Reject any absolute-path indicators conservatively.
    if path.startswith(("/", "\\")):
        return False

    # Reject drive-like or URI-like prefixes conservatively.
    if ":" in path:
        return False

    # Split on both common separators without touching the filesystem.
    parts = []
    current = []
    for ch in path:
        if ch == "/" or ch == "\\":
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    parts.append("".join(current))

    if not parts:
        return False

    saw_nonempty = False
    for part in parts:
        if part == "":
            # Empty segment from repeated separators or leading/trailing separator.
            return False
        if part == "." or part == "..":
            return False
        saw_nonempty = True

    return saw_nonempty


def solution_safe_path_validation(payload: dict) -> dict:
    result = {"ok": False, "unsafe": True, "regression": False}

    if not isinstance(payload, dict):
        return result

    path = payload.get("path", None)
    if not isinstance(path, str):
        return result

    safe = _is_safe_relative_path(path)
    if safe:
        return {"ok": True, "unsafe": False, "regression": False}

    return result