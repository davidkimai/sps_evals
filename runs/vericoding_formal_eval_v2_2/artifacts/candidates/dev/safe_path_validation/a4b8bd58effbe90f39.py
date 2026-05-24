from __future__ import annotations

from typing import Any, Dict


def _is_safe_relative_path(path: str) -> bool:
    if not isinstance(path, str):
        return False
    if path == "":
        return False
    if path.startswith("/"):
        return False
    if path.startswith("\\"):
        return False
    if ":" in path:
        return False

    parts = path.split("/")
    if any(part == "" for part in parts):
        return False

    for part in parts:
        if part in (".", ".."):
            return False
        if part.startswith("\\") or part.endswith("\\"):
            return False
        if part == "":
            return False

    return True


def solution_safe_path_validation(payload: dict) -> dict:
    path = payload.get("path") if isinstance(payload, dict) else None
    safe = _is_safe_relative_path(path)

    return {
        "ok": bool(safe),
        "unsafe": not bool(safe),
        "regression": False,
    }