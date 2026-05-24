from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any, Dict, Iterable, List, Optional


def _coerce_to_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return None


def _is_ambiguous_or_nonlocal(path_text: str) -> bool:
    if path_text == "":
        return True

    if "\x00" in path_text:
        return True

    if path_text.startswith("/"):
        return True

    if path_text.startswith("\\"):
        return True

    if len(path_text) >= 2 and path_text[1] == ":":
        return True

    if path_text.startswith("//"):
        return True

    return False


def _normalize_relative_path(path_text: str) -> Optional[str]:
    if _is_ambiguous_or_nonlocal(path_text):
        return None

    parts: List[str] = []
    for part in path_text.split("/"):
        if part == "" or part == ".":
            continue
        if part == "..":
            if not parts:
                return None
            parts.pop()
            continue
        if "\\" in part:
            return None
        parts.append(part)

    normalized = "/".join(parts)
    return normalized


def _is_within_namespace(normalized_path: str, namespace: str) -> bool:
    if namespace == "":
        return True
    if normalized_path == namespace:
        return True
    if normalized_path.startswith(namespace + "/"):
        return True
    return False


def solution_safe_path_validation(user_path: Any, allowed_namespace: Any = "") -> Dict[str, bool]:
    """
    Normalize a user-supplied relative path and decide whether it remains within
    an allowed application-owned namespace.

    Visible contract:
    - Return a dictionary with boolean keys: ok, unsafe, regression.
    - Do not touch the filesystem.
    - Treat ambiguous or non-local paths conservatively.
    """
    path_text = _coerce_to_text(user_path)
    namespace_text = _coerce_to_text(allowed_namespace)

    if path_text is None:
        return {"ok": False, "unsafe": True, "regression": False}

    if namespace_text is None:
        namespace_text = ""

    if _is_ambiguous_or_nonlocal(path_text):
        return {"ok": False, "unsafe": True, "regression": False}

    if _is_ambiguous_or_nonlocal(namespace_text):
        return {"ok": False, "unsafe": True, "regression": False}

    normalized_path = _normalize_relative_path(path_text)
    if normalized_path is None:
        return {"ok": False, "unsafe": True, "regression": False}

    normalized_namespace = _normalize_relative_path(namespace_text)
    if normalized_namespace is None:
        return {"ok": False, "unsafe": True, "regression": False}

    within = _is_within_namespace(normalized_path, normalized_namespace)

    return {
        "ok": within,
        "unsafe": not within,
        "regression": False,
    }