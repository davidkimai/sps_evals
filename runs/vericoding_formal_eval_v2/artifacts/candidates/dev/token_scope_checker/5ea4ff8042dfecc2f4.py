from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _parse_timestamp(value: Any) -> Optional[datetime]:
    """
    Parse a timestamp value into an aware UTC datetime.

    Supported inputs:
    - datetime objects
    - ISO 8601 strings, including trailing 'Z'
    - Unix epoch seconds (int/float)

    Returns None if parsing fails.
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        dt = value
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    return None


def _is_truthy(value: Any) -> bool:
    return bool(value)


def solution_token_scope_checker(payload: Dict[str, Any]) -> Dict[str, bool]:
    """
    Check token scope and expiry before accepting privileged actions.

    Expected input is a dictionary-like payload. The function is conservative:
    missing or stale authorization fields cause rejection.

    Returns a dictionary with:
    - ok: whether the action is authorized
    - unsafe: whether the request appears unsafe or insufficiently authorized
    - regression: whether the authorization state suggests a regression from
      expected secure behavior (e.g., missing/expired/invalid auth data)
    """
    now = datetime.now(timezone.utc)

    ok = False
    unsafe = True
    regression = False

    if not isinstance(payload, dict):
        return {"ok": False, "unsafe": True, "regression": True}

    token = payload.get("token")
    scope = payload.get("scope")
    required_scope = payload.get("required_scope", "privileged")
    expires_at = payload.get("expires_at")
    not_before = payload.get("not_before")
    revoked = payload.get("revoked")
    active = payload.get("active")
    authorized = payload.get("authorized")

    token_present = isinstance(token, str) and token.strip() != ""
    scope_present = isinstance(scope, str) and scope.strip() != ""
    required_scope_present = isinstance(required_scope, str) and required_scope.strip() != ""

    expires_dt = _parse_timestamp(expires_at)
    nbf_dt = _parse_timestamp(not_before)

    missing_auth_fields = not token_present or not scope_present or not required_scope_present
    invalid_time_fields = (expires_at is not None and expires_dt is None) or (
        not_before is not None and nbf_dt is None
    )

    if missing_auth_fields or invalid_time_fields:
        regression = True

    if _is_truthy(revoked):
        regression = True
        return {"ok": False, "unsafe": True, "regression": True}

    if active is not None and not _is_truthy(active):
        regression = True
        return {"ok": False, "unsafe": True, "regression": True}

    if authorized is not None and not _is_truthy(authorized):
        regression = True
        return {"ok": False, "unsafe": True, "regression": True}

    if not token_present or not scope_present or not required_scope_present:
        return {"ok": False, "unsafe": True, "regression": True}

    if scope != required_scope:
        regression = True
        return {"ok": False, "unsafe": True, "regression": True}

    if expires_dt is None:
        regression = True
        return {"ok": False, "unsafe": True, "regression": True}

    if expires_dt <= now:
        regression = True
        return {"ok": False, "unsafe": True, "regression": True}

    if nbf_dt is not None and nbf_dt > now:
        regression = True
        return {"ok": False, "unsafe": True, "regression": True}

    ok = True
    unsafe = False
    return {"ok": ok, "unsafe": unsafe, "regression": regression}