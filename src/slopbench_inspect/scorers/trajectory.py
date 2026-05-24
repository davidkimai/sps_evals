from __future__ import annotations

from statistics import mean
from typing import Any


def summarize_trajectory_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a small sanitized trajectory summary from checkpoint rows."""
    if not rows:
        return {
            "row_count": 0,
            "final_pass": False,
            "row_pass_rate": 0.0,
            "avg_cc_average": None,
            "pathology_rate": 0.0,
        }
    cc_values = [
        float(row["cc_average"])
        for row in rows
        if row.get("cc_average") not in {None, ""}
    ]
    pathology_rows = [
        row
        for row in rows
        if str(row.get("failure_type") or "").startswith(("syntax_error", "sandbox_error"))
    ]
    return {
        "row_count": len(rows),
        "final_pass": bool(rows[-1].get("pass_bool")),
        "row_pass_rate": sum(1 for row in rows if row.get("pass_bool")) / len(rows),
        "avg_cc_average": round(mean(cc_values), 6) if cc_values else None,
        "pathology_rate": round(len(pathology_rows) / len(rows), 6),
    }
