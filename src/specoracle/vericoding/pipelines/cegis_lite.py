from __future__ import annotations

from typing import Any

from specoracle.vericoding.schemas import REPAIR_PROMPT_VERSION, stable_hash


def repair_selected_candidate(row: dict[str, Any]) -> dict[str, Any]:
    """Return an unrepaired copy unless a live repair artifact is supplied.

    v2 live repair is implemented in ``program_live``. This legacy helper must
    not flip hidden labels or hidden pass/fail fields.
    """
    repaired = dict(row)
    if row.get("repaired_artifact_path") and row.get("reevaluation_row_id"):
        repaired["candidate_id"] = f"{row['candidate_id']}:repair1"
        repaired["repair_prompt_version"] = REPAIR_PROMPT_VERSION
        repaired["repair_row_hash"] = stable_hash(
            {
                "candidate_id": repaired["candidate_id"],
                "repaired_artifact_path": row.get("repaired_artifact_path"),
                "reevaluation_row_id": row.get("reevaluation_row_id"),
            },
            length=16,
        )
    return repaired
