from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any, Dict, Iterable, List, Tuple


def _coerce_to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", "surrogatepass")
        except Exception:
            return value.decode("utf-8", "replace")
    return str(value)


def _split_namespace(raw: str) -> Tuple[str, str]:
    """
    Split an input into:
      - namespace prefix (before the first slash, if any)
      - remainder path
    If there is no slash, the whole string is treated as the namespace token.
    """
    if "/" not in raw:
        return raw, ""
    head, tail = raw.split("/", 1)
    return head, tail


def _has_unsafe_prefix(raw: str) -> bool:
    if not raw:
        return True
    if raw.startswith("/") or raw.startswith("\\"):
        return True
    if raw.startswith("~"):
        return True
    if ":" in raw:
        return True
    if "\x00" in raw:
        return True
    return False


def _normalize_relative_path(path_text: str) -> Tuple[str, bool]:
    """
    Normalize a relative path using POSIX semantics.
    Returns (normalized_path, escaped_root).
    """
    parts: List[str] = []
    escaped = False

    for part in PurePosixPath(path_text).parts:
        if part in ("", "."):
            continue
        if part == "..":
            if parts:
                parts.pop()
            else:
                escaped = True
            continue
        parts.append(part)

    return "/".join(parts), escaped


def _is_local_relative(raw: str) -> bool:
    if _has_unsafe_prefix(raw):
        return False
    if "\\" in raw:
        return False
    return True


def _build_result(ok: bool, unsafe: bool, regression: bool) -> Dict[str, bool]:
    return {"ok": ok, "unsafe": unsafe, "regression": regression}


def solution_safe_path_validation(user_path: Any) -> Dict[str, bool]:
    """
    Normalize a user-supplied relative path and decide whether it remains within
    an allowed application-owned namespace.

    Contract:
      - returns dict with boolean keys: ok, unsafe, regression
      - does not touch the filesystem
      - treats ambiguous or non-local paths conservatively
    """
    raw = _coerce_to_text(user_path).strip()

    if not raw:
        return _build_result(ok=False, unsafe=True, regression=False)

    if not _is_local_relative(raw):
        return _build_result(ok=False, unsafe=True, regression=False)

    namespace, remainder = _split_namespace(raw)

    # Conservative handling for namespace-like inputs:
    # If the first segment looks like a traversal or empty token, reject.
    if namespace in ("", ".", ".."):
        return _build_result(ok=False, unsafe=True, regression=False)

    normalized_remainder, escaped = _normalize_relative_path(remainder)

    if escaped:
        return _build_result(ok=False, unsafe=True, regression=False)

    # Reconstruct a canonical application-owned namespace path.
    if normalized_remainder:
        normalized = f"{namespace}/{normalized_remainder}"
    else:
        normalized = namespace

    # Any path that normalizes to empty or contains traversal remnants is unsafe.
    if not normalized or normalized.startswith("../") or normalized == "..":
        return _build_result(ok=False, unsafe=True, regression=False)

    # Regression flag is reserved for cases where the input appears local but
    # normalization materially changes it in a way that could affect policy.
    regression = normalized != raw

    # The path is considered safe if it stayed within the namespace and did not
    # require escaping above the namespace root.
    return _build_result(ok=True, unsafe=False, regression=regression)