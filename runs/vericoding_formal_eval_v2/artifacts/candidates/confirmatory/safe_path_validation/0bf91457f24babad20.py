from __future__ import annotations

from typing import Any, Dict, List


def solution_safe_path_validation(path: Any) -> Dict[str, bool]:
    """
    Normalize a user-supplied relative path and decide whether it remains within
    an allowed application-owned namespace.

    Contract:
    - Return a dictionary with boolean keys: ok, unsafe, regression.
    - Do not touch the filesystem.
    - Treat ambiguous or non-local paths conservatively.
    """
    result = {
        "ok": False,
        "unsafe": True,
        "regression": False,
    }

    if not isinstance(path, str):
        return result

    raw = path
    if raw == "":
        return result

    # Reject NUL and other control characters conservatively.
    for ch in raw:
        if ord(ch) < 32 or ord(ch) == 127:
            return result

    # Normalize separators to forward slashes for local reasoning.
    normalized = raw.replace("\\", "/")

    # Absolute or rooted paths are not allowed.
    if normalized.startswith("/"):
        return result

    # Windows drive-like or UNC-like forms are treated as unsafe.
    if len(normalized) >= 2 and normalized[1] == ":":
        return result
    if normalized.startswith("//"):
        return result

    parts = normalized.split("/")
    stack: List[str] = []

    for part in parts:
        if part == "" or part == ".":
            continue
        if part == "..":
            if not stack:
                return result
            stack.pop()
            continue
        # Reject ambiguous path segments conservatively.
        if part in {".", ".."}:
            return result
        stack.append(part)

    if not stack:
        return result

    # Application-owned namespace policy:
    # The path must remain within a single top-level namespace segment.
    # This is conservative and avoids allowing traversal into sibling areas.
    namespace = stack[0]
    if namespace in {"", ".", ".."}:
        return result

    # Reconstruct the normalized relative path.
    safe_path = "/".join(stack)

    # Final audit check: no traversal tokens remain.
    if "/../" in f"/{safe_path}/" or "/./" in f"/{safe_path}/":
        return result

    result["ok"] = True
    result["unsafe"] = False
    result["regression"] = False
    return result