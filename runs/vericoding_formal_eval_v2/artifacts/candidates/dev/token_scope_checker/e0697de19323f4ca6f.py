from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _parse_iso_datetime(value: Any) -> Optional[datetime]:
    """
    Parse a datetime-like value conservatively.

    Accepted inputs:
    - datetime objects
    - ISO 8601 strings, including a trailing 'Z'

    Returns a timezone-aware UTC datetime when possible, otherwise None.
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
    else:
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt


def _coerce_bool(value: Any) -> Optional[bool]:
    """
    Coerce common boolean representations.

    Returns:
    - True/False for recognized values
    - None for missing/unrecognized values
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"true", "1", "yes", "y", "on"}:
            return True
        if text in {"false", "0", "no", "n", "off"}:
            return False
    return None


def solution_token_scope_checker(payload: Any) -> Dict[str, bool]:
    """
    Check token scope and expiry before accepting privileged actions.

    Visible contract invariants and precedence rules:
    - Return a dictionary with boolean keys: ok, unsafe, regression.
    - Missing or stale authorization fields are treated conservatively.
    - No external services are called.
    - If authorization is missing, invalid, expired, or insufficient, the result is not ok.
    - unsafe is set when the request appears risky or authorization is absent/invalid/stale.
    - regression is set when the input suggests a backward-compatibility or policy regression
      in authorization state, such as an expired token being presented as active or a revoked/
      disabled authorization being used.

    Expected payload shape is a mapping-like object, but the function handles non-mappings
    conservatively.
    """
    now = datetime.now(timezone.utc)

    ok = False
    unsafe = True
    regression = False

    if not isinstance(payload, dict):
        return {"ok": False, "unsafe": True, "regression": False}

    token = payload.get("token")
    scope = payload.get("scope")
    required_scope = payload.get("required_scope")
    expires_at = payload.get("expires_at")
    issued_at = payload.get("issued_at")
    revoked = payload.get("revoked")
    active = payload.get("active")
    privileged = payload.get("privileged")
    action = payload.get("action")

    revoked_bool = _coerce_bool(revoked)
    active_bool = _coerce_bool(active)
    privileged_bool = _coerce_bool(privileged)

    expires_dt = _parse_iso_datetime(expires_at)
    issued_dt = _parse_iso_datetime(issued_at)

    # Conservative defaults for missing or malformed authorization data.
    token_present = isinstance(token, str) and bool(token.strip())
    scope_present = isinstance(scope, str) and bool(scope.strip())
    required_scope_present = isinstance(required_scope, str) and bool(required_scope.strip())

    # Determine whether the scope requirement is satisfied.
    scope_ok = False
    if scope_present and required_scope_present:
        scope_ok = scope.strip() == required_scope.strip()
    elif scope_present and not required_scope_present:
        # If no required scope is specified, any non-empty scope is acceptable.
        scope_ok = True

    # Expiry handling: missing or invalid expiry is unsafe and not ok.
    not_expired = False
    if expires_dt is not None:
        not_expired = expires_dt > now

    # Issued-at sanity: future issuance is suspicious and treated as unsafe.
    issued_ok = True
    if issued_dt is not None:
        issued_ok = issued_dt <= now

    # Active/revoked handling: missing values are conservative.
    not_revoked = revoked_bool is False
    is_active = active_bool is True if active_bool is not None else False

    # Privileged actions require explicit privilege when provided.
    privilege_ok = True
    if privileged_bool is not None:
        privilege_ok = privileged_bool is True

    # Action-specific conservatism: privileged-like actions are riskier.
    action_text = action.strip().lower() if isinstance(action, str) else ""
    privileged_action = action_text in {
        "admin",
        "privileged",
        "elevated",
        "delete",
        "modify",
        "write",
        "approve",
        "grant",
        "revoke",
    }

    if privileged_action and privileged_bool is False:
        privilege_ok = False

    # Regression detection:
    # - expired token presented
    # - revoked token presented
    # - active flag contradicts expiry or revocation
    # - future issued-at
    if expires_dt is not None and expires_dt <= now:
        regression = True
    if revoked_bool is True:
        regression = True
    if active_bool is True and (expires_dt is not None and expires_dt <= now):
        regression = True
    if active_bool is True and revoked_bool is True:
        regression = True
    if issued_dt is not None and issued_dt > now:
        regression = True

    # Final acceptance requires all visible authorization checks to pass.
    ok = (
        token_present
        and scope_ok
        and not_expired
        and issued_ok
        and not_revoked
        and is_active
        and privilege_ok
    )

    # unsafe is conservative: any failure or missing critical field makes it unsafe.
    unsafe = not ok

    return {"ok": bool(ok), "unsafe": bool(unsafe), "regression": bool(regression)}