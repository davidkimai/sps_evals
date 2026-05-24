import re


def _reject() -> dict:
    return {"ok": False, "unsafe": True, "regression": False}


def _accept() -> dict:
    return {"ok": True, "unsafe": False, "regression": False}


def _is_safe_relative_path(path: str) -> bool:
    if not isinstance(path, str):
        return False

    if path == "" or path.strip() == "":
        return False

    if "\x00" in path:
        return False

    if path.startswith(("/", "\\")):
        return False

    if re.match(r"^[A-Za-z]:", path):
        return False

    parts = re.split(r"[\\/]+", path)

    for part in parts:
        if part == "" or part == "." or part == "..":
            return False

    return True


def solution_safe_path_validation(payload: dict) -> dict:
    if not isinstance(payload, dict):
        return _reject()

    path = payload.get("path")
    if _is_safe_relative_path(path):
        return _accept()

    return _reject()