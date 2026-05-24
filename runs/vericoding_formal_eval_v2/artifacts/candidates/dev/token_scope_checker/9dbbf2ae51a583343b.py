from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            if text.endswith("Z"):
                try:
                    dt = datetime.fromisoformat(text[:-1] + "+00:00")
                except ValueError:
                    return None
            else:
                return None
    else:
        return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def solution_token_scope_checker(payload: dict) -> dict:
    result: Dict[str, bool] = {"ok": False, "unsafe": False, "regression": False}

    if not isinstance(payload, dict):
        result["unsafe"] = True
        return result

    required_scope = payload.get("required_scope")
    scope = payload.get("scope")
    expires_at = payload.get("expires_at")

    if required_scope is None or scope is None or expires_at is None:
        result["unsafe"] = True
        return result

    if scope != required_scope:
        result["unsafe"] = True
        return result

    dt = _parse_datetime(expires_at)
    if dt is None:
        result["unsafe"] = True
        return result

    now = datetime.now(timezone.utc)
    if dt <= now:
        result["unsafe"] = True
        return result

    result["ok"] = True
    return result