from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _parse_timestamp(value: Any) -> Optional[datetime]:
    """
    Parse a timestamp value into an aware UTC datetime.

    Supported inputs:
    - datetime objects
    - ISO 8601 strings, including a trailing 'Z'
    - numeric Unix timestamps (int/float)

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


def solution_token_scope_checker(payload: Any) -> Dict[str, bool]:
    """
    Check token scope and expiry before accepting privileged actions.

    Visible contract:
    - Return a dictionary with boolean ok, unsafe, and regression fields.
    - Treat missing or stale authorization fields conservatively.
    - Do not call external services.

    Interpretation:
    - ok: authorization is present, unexpired, and includes a privileged scope.
    - unsafe: authorization is missing, malformed, stale, or otherwise insufficient.
    - regression: indicates a conservative fallback / degraded trust state when
      authorization data is incomplete or stale. This is set when the input does
      not provide enough reliable authorization information, including missing
      fields or expired tokens.
    """
    result = {"ok": False, "unsafe": True, "regression": True}

    if not isinstance(payload, dict):
        return result

    auth = payload.get("authorization")
    if not isinstance(auth, dict):
        return result

    token = auth.get("token")
    scopes = auth.get("scopes")
    expires_at = auth.get("expires_at")
    issued_at = auth.get("issued_at")

    now = datetime.now(timezone.utc)

    expiry_dt = _parse_timestamp(expires_at)
    issued_dt = _parse_timestamp(issued_at)

    # Conservative handling for missing or malformed fields.
    if token is None or not isinstance(token, str) or not token.strip():
        return result

    if expiry_dt is None:
        return result

    if expiry_dt <= now:
        return result

    # If issued_at is present, ensure it is not in the future and not after expiry.
    if issued_dt is not None:
        if issued_dt > now:
            return result
        if issued_dt > expiry_dt:
            return result

    # Scope validation: require at least one privileged scope.
    privileged_scopes = {"admin", "write", "privileged", "elevated", "scope:admin"}
    scope_set = set()

    if isinstance(scopes, str):
        scope_set = {s for s in scopes.replace(",", " ").split() if s}
    elif isinstance(scopes, (list, tuple, set)):
        for item in scopes:
            if isinstance(item, str) and item.strip():
                scope_set.add(item.strip())
    else:
        return result

    if not scope_set.intersection(privileged_scopes):
        return result

    # Authorization is sufficiently valid.
    return {"ok": True, "unsafe": False, "regression": False}