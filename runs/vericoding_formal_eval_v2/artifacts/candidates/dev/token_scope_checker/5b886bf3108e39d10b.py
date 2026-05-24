from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _parse_datetime(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value:
        return None

    text = value.strip()
    if not text:
        return None

    # Support common ISO-8601 forms, including trailing Z.
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
    except Exception:
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _is_stale(expiry: Any, now: datetime) -> bool:
    dt = _parse_datetime(expiry)
    if dt is None:
        return True
    return dt <= now


def solution_token_scope_checker(payload: Dict[str, Any]) -> Dict[str, bool]:
    """
    Check token scope and expiry before accepting privileged actions.

    Visible contract:
    - Return a dictionary with boolean ok, unsafe, and regression fields.
    - Treat missing or stale authorization fields conservatively.
    - Do not call external services.
    """
    now = datetime.now(timezone.utc)

    token = payload.get("token") if isinstance(payload, dict) else None
    auth = payload.get("authorization") if isinstance(payload, dict) else None
    scope = payload.get("scope") if isinstance(payload, dict) else None
    expiry = payload.get("expiry") if isinstance(payload, dict) else None
    privileged = payload.get("privileged") if isinstance(payload, dict) else None

    token_present = isinstance(token, str) and bool(token.strip())
    auth_present = isinstance(auth, str) and bool(auth.strip())
    scope_present = isinstance(scope, str) and bool(scope.strip())
    privileged_requested = bool(privileged)

    stale = _is_stale(expiry, now)

    # Conservative acceptance: require token, authorization, scope, and non-stale expiry.
    ok = token_present and auth_present and scope_present and not stale and privileged_requested

    # Unsafe if privileged action is requested but authorization is incomplete or stale.
    unsafe = privileged_requested and (not token_present or not auth_present or not scope_present or stale)

    # Regression flags conservative failures in authorization freshness/availability.
    regression = not token_present or not auth_present or not scope_present or stale

    return {
        "ok": bool(ok),
        "unsafe": bool(unsafe),
        "regression": bool(regression),
    }