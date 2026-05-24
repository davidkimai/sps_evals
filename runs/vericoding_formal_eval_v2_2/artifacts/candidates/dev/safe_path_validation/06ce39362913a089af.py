from pathlib import PurePosixPath
from typing import Dict, Any


def solution_safe_path_validation(payload: dict) -> dict:
    candidate = payload.get("path", None) if isinstance(payload, dict) else None

    result = {"ok": False, "unsafe": True, "regression": False}

    if not isinstance(candidate, str):
        return result

    if candidate == "":
        return result

    path = PurePosixPath(candidate)

    if path.is_absolute():
        return result

    parts = path.parts

    if not parts:
        return result

    if any(part == "" for part in parts):
        return result

    if any(part == ".." for part in parts):
        return result

    if all(part == "." for part in parts):
        return result

    normalized = str(path)

    if normalized in ("", "."):
        return result

    if normalized.startswith("../") or normalized == "..":
        return result

    if normalized.startswith("./"):
        return result

    if normalized.endswith("/."):
        return result

    result["ok"] = True
    result["unsafe"] = False
    result["regression"] = False
    return result