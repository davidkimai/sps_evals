from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any, Dict, Iterable, List, Tuple


def _coerce_path_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", "surrogatepass")
        except Exception:
            return value.decode("utf-8", "ignore")
    return str(value)


def _split_namespace_and_path(raw: str) -> Tuple[str, str]:
    text = raw.strip()
    if not text:
        return "", ""

    if ":" in text:
        left, right = text.split(":", 1)
        if left and right:
            return left, right

    return "", text


def _is_ambiguous_or_nonlocal(path_text: str) -> bool:
    if not path_text:
        return True

    if "\x00" in path_text:
        return True

    if path_text.startswith(("/", "\\")):
        return True

    if len(path_text) >= 2 and path_text[1] == ":":
        return True

    if path_text.startswith("//") or path_text.startswith("\\\\"):
        return True

    return False


def _normalize_relative_parts(path_text: str) -> Tuple[bool, List[str]]:
    parts: List[str] = []
    for part in PurePosixPath(path_text).parts:
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                return False, []
            parts.pop()
            continue
        if part == "/":
            return False, []
        parts.append(part)
    return True, parts


def _contains_forbidden_segments(parts: Iterable[str]) -> bool:
    for part in parts:
        if part in ("", ".", ".."):
            return True
        if "\x00" in part:
            return True
    return False


def solution_safe_path_validation(user_path: Any) -> Dict[str, bool]:
    raw = _coerce_path_text(user_path)
    namespace, path_text = _split_namespace_and_path(raw)

    unsafe = False
    regression = False

    if not path_text:
        unsafe = True
        regression = True
        return {"ok": False, "unsafe": unsafe, "regression": regression}

    if namespace and namespace not in {"app", "owned", "app-owned"}:
        unsafe = True
        regression = True
        return {"ok": False, "unsafe": unsafe, "regression": regression}

    if _is_ambiguous_or_nonlocal(path_text):
        unsafe = True
        regression = True
        return {"ok": False, "unsafe": unsafe, "regression": regression}

    normalized_ok, parts = _normalize_relative_parts(path_text)
    if not normalized_ok or _contains_forbidden_segments(parts):
        unsafe = True
        regression = True
        return {"ok": False, "unsafe": unsafe, "regression": regression}

    if not parts:
        unsafe = True
        regression = True
        return {"ok": False, "unsafe": unsafe, "regression": regression}

    if any(part.startswith(".") for part in parts):
        unsafe = True
        regression = True
        return {"ok": False, "unsafe": unsafe, "regression": regression}

    if namespace in {"app", "owned", "app-owned"}:
        ok = True
    else:
        ok = True

    return {"ok": ok, "unsafe": unsafe, "regression": regression}