from __future__ import annotations

from typing import Any, Dict, List


def _is_valid_segment(segment: str) -> bool:
    if segment == "":
        return False
    if segment == "." or segment == "..":
        return False
    return True


def _validate_relative_path(path: Any) -> bool:
    if not isinstance(path, str):
        return False

    if path == "":
        return False

    if path.strip() == "":
        return False

    if path.startswith("/"):
        return False

    if path.startswith("\\"):
        return False

    if ":" in path:
        return False

    if "\x00" in path:
        return False

    parts = path.split("/")

    for part in parts:
        if not _is_valid_segment(part):
            return False

    if path.endswith("/"):
        return False

    return True


def solution_safe_path_validation(payload: dict) -> dict:
    ok = False
    unsafe = True
    regression = False

    if isinstance(payload, dict):
        path = payload.get("path")
        safe = _validate_relative_path(path)
        ok = bool(safe)
        unsafe = not safe

    return {
        "ok": ok,
        "unsafe": unsafe,
        "regression": regression,
    }