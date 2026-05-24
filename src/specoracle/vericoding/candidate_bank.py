from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from specoracle.metrics import build_structural_metric_record
from specoracle.vericoding.mutations import blueprints_for_surface, render_candidate_code
from specoracle.vericoding.schemas import (
    GENERATION_PROMPT_VERSION,
    PROGRAM_VERSION,
    CandidateBankRow,
    VericodingPaths,
    append_jsonl,
    dataclass_to_dict,
    file_sha256,
    now_iso,
    read_jsonl,
    stable_hash,
    validate_dataclass_row,
)

MIN_CANDIDATES_BY_SURFACE = {
    "internal": 8,
    "secure": 8,
    "scbench_regression": 6,
    "terminalbench_guardrail": 6,
}


def build_candidate_bank(
    task_pool: dict[str, Any],
    *,
    paths: VericodingPaths = VericodingPaths(),
) -> list[dict[str, Any]]:
    """Build deterministic candidate-bank rows and append only missing rows."""
    ledger_path = paths.ledgers_dir / "candidate_bank.jsonl"
    existing = read_jsonl(ledger_path)
    existing_ids = {row["bank_row_id"] for row in existing}
    rows: list[dict[str, Any]] = []
    git_commit = _git("rev-parse", "--short", "HEAD") or "unknown"
    git_dirty = bool(_git("status", "--short"))
    candidate_dir = paths.wrangled_dir / "candidates"
    candidate_dir.mkdir(parents=True, exist_ok=True)

    for task in task_pool["tasks"]:
        surface = str(task["surface"])
        minimum = MIN_CANDIDATES_BY_SURFACE[surface]
        for index, blueprint in enumerate(blueprints_for_surface(surface, minimum)):
            candidate_id = f"{task['task_id']}:{blueprint.suffix}:{index}"
            bank_row_id = stable_hash(
                {
                    "program_version": PROGRAM_VERSION,
                    "task_id": task["task_id"],
                    "candidate_id": candidate_id,
                },
                length=16,
            )
            if bank_row_id in existing_ids:
                continue
            artifact_path = candidate_dir / f"{bank_row_id}.py"
            code = render_candidate_code(str(task["task_id"]), blueprint)
            artifact_path.write_text(code, encoding="utf-8")
            metrics = build_structural_metric_record(code, language="python")
            row = CandidateBankRow(
                program_version=PROGRAM_VERSION,
                bank_row_id=bank_row_id,
                surface=task["surface"],
                split=task["split"],
                task_id=task["task_id"],
                stable_sample_id=task["stable_sample_id"],
                candidate_id=candidate_id,
                candidate_source=blueprint.source,
                candidate_lineage=f"deterministic_mutation:{blueprint.suffix}",
                generator_condition=_generator_condition(blueprint.source),
                generator_model="deterministic-fixture",
                prompt_template_version=GENERATION_PROMPT_VERSION,
                temperature=None,
                seed=index,
                raw_artifact_policy="tracked_generated_candidate_no_external_raw_prompt",
                candidate_artifact_path=str(artifact_path),
                candidate_sha256=file_sha256(artifact_path),
                visible_compile_pass=blueprint.parse_ok,
                visible_tests_pass=blueprint.visible_tests_pass,
                hidden_tests_pass=blueprint.hidden_tests_pass,
                property_checks_pass=blueprint.property_checks_pass,
                regression_checks_pass=blueprint.regression_checks_pass,
                security_checks_pass=blueprint.security_checks_pass,
                parse_ok=bool(metrics["parse_ok"]) and blueprint.parse_ok,
                cc_average=_metric_number(metrics.get("cc_average"), blueprint.cc_average),
                max_nesting_depth=int(
                    _metric_number(metrics.get("max_nesting_depth"), blueprint.max_nesting_depth)
                ),
                maintainability_index=_metric_number(
                    metrics.get("maintainability_index"),
                    blueprint.maintainability_index,
                ),
                redundancy_score=_metric_number(
                    metrics.get("redundancy_score"),
                    blueprint.redundancy_score,
                ),
                candidate_label=blueprint.label,  # type: ignore[arg-type]
                deceptive_candidate=blueprint.deceptive,
                insecure_candidate=blueprint.insecure,
                regression_candidate=blueprint.regression,
                cost_usd=0.0,
                input_tokens=0,
                output_tokens=0,
                runner_git_commit=git_commit,
                runner_git_dirty=git_dirty,
                created_at=now_iso(),
            )
            validate_dataclass_row(row)
            rows.append(dataclass_to_dict(row))
    append_jsonl(ledger_path, rows)
    return existing + rows


def candidate_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["surface"], row["split"])
        item = summary.setdefault(
            key,
            {
                "surface": row["surface"],
                "split": row["split"],
                "candidates": 0,
                "correct": 0,
                "deceptive": 0,
                "security_fail": 0,
                "regression_fail": 0,
                "syntax_fail": 0,
            },
        )
        item["candidates"] += 1
        item[str(row["candidate_label"])] = item.get(str(row["candidate_label"]), 0) + 1
        if row.get("deceptive_candidate"):
            item["deceptive"] += 1
    return sorted(summary.values(), key=lambda item: (item["surface"], item["split"]))


def _generator_condition(source: str) -> str:
    if source == "reference_oracle":
        return "spec_conditioned_prompt"
    if source in {"structural_discipline", "structurally_neat_wrong"}:
        return "structural_discipline_prompt"
    if source == "overfit_bloat":
        return "baseline_prompt"
    return "deterministic_mutation"


def _metric_number(value: Any, fallback: float) -> float:
    return float(value) if isinstance(value, int | float) else float(fallback)


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=Path(__file__).resolve().parents[3],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()
