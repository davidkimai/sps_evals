from __future__ import annotations

from collections import defaultdict
from typing import Any

from specoracle.vericoding.pipelines.cegis_lite import repair_selected_candidate
from specoracle.vericoding.schemas import (
    SELECTOR_PROMPT_VERSION,
    E2ERow,
    SelectorEvalRow,
    dataclass_to_dict,
    now_iso,
    stable_hash,
    validate_dataclass_row,
)
from specoracle.vericoding.selectors import SELECTORS


def run_selector_eval(
    candidate_rows: list[dict[str, Any]],
    *,
    split: str | None = None,
    selector_names: list[str] | None = None,
) -> list[dict[str, Any]]:
    by_task = _group_by_task(candidate_rows, split=split)
    names = selector_names or list(SELECTORS)
    out: list[dict[str, Any]] = []
    for (surface, task_split, task_id), pool in sorted(by_task.items()):
        for name in names:
            selected = SELECTORS[name](pool, task_id=task_id)
            row = SelectorEvalRow(
                selector_eval_row_id=stable_hash(
                    {
                        "surface": surface,
                        "split": task_split,
                        "task_id": task_id,
                        "selector": name,
                    },
                    length=18,
                ),
                surface=surface,
                split=task_split,
                task_id=task_id,
                selector_name=name,
                candidate_pool_size=len(pool),
                selected_candidate_id=selected["candidate_id"],
                selected_label=selected["candidate_label"],
                selected_visible_tests_pass=bool(selected["visible_tests_pass"]),
                selected_hidden_tests_pass=bool(selected["hidden_tests_pass"]),
                selected_security_checks_pass=bool(selected["security_checks_pass"]),
                selected_regression_checks_pass=bool(selected["regression_checks_pass"]),
                selection_correct=selected["candidate_label"] == "correct",
                false_accept=_false_accept(selected),
                secure_false_accept=_secure_false_accept(selected),
                regression_false_accept=_regression_false_accept(selected),
                selector_cost_usd=0.0,
                selector_input_tokens=0,
                selector_output_tokens=0,
                selector_prompt_version=SELECTOR_PROMPT_VERSION,
                comparison_count=max(0, min(len(pool), 4) - 1) if name == "specoracle_selector" else 0,
                created_at=now_iso(),
            )
            validate_dataclass_row(row)
            out.append(dataclass_to_dict(row))
    return out


def run_vericoding_e2e(
    candidate_rows: list[dict[str, Any]],
    *,
    split: str = "confirmatory",
    pipeline_names: list[str] | None = None,
) -> list[dict[str, Any]]:
    pipelines = pipeline_names or [
        "single_sample",
        "best_of_n_random",
        "best_of_n_tests_only",
        "best_of_n_structural_only",
        "best_of_n_llm_judge",
        "best_of_n_specoracle",
        "best_of_n_specoracle_plus_one_repair",
    ]
    by_task = _group_by_task(candidate_rows, split=split)
    out: list[dict[str, Any]] = []
    for (surface, task_split, task_id), pool in sorted(by_task.items()):
        n = 3 if surface == "terminalbench_guardrail" else 4
        pool_n = pool[:n]
        for pipeline in pipelines:
            selected, repair_applied = _select_for_pipeline(pipeline, pool_n, task_id=task_id)
            row = E2ERow(
                e2e_row_id=stable_hash(
                    {
                        "surface": surface,
                        "split": task_split,
                        "task_id": task_id,
                        "pipeline": pipeline,
                    },
                    length=18,
                ),
                surface=surface,
                split=task_split,
                task_id=task_id,
                pipeline_name=pipeline,
                n_candidates=len(pool_n),
                selected_candidate_id=selected["candidate_id"],
                repair_applied=repair_applied,
                final_visible_tests_pass=bool(selected["visible_tests_pass"]),
                final_hidden_tests_pass=bool(selected["hidden_tests_pass"]),
                final_security_checks_pass=bool(selected["security_checks_pass"]),
                final_regression_checks_pass=bool(selected["regression_checks_pass"]),
                final_success=_final_success(selected),
                false_accept=_false_accept(selected),
                cost_usd=float(selected.get("cost_usd") or 0.0),
                input_tokens=int(selected.get("input_tokens") or 0),
                output_tokens=int(selected.get("output_tokens") or 0),
                wall_seconds=0.0,
                created_at=now_iso(),
            )
            out.append(dataclass_to_dict(row))
    return out


def selector_metrics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["split"], row["selector_name"])].append(row)
    out = []
    for (split, selector), group in sorted(grouped.items()):
        count = len(group)
        out.append(
            {
                "split": split,
                "selector_name": selector,
                "rows": count,
                "top1_accuracy": _mean(group, "selection_correct"),
                "false_accept_rate": _mean(group, "false_accept"),
                "secure_false_accept_rate": _mean(group, "secure_false_accept"),
                "regression_false_accept_rate": _mean(group, "regression_false_accept"),
            }
        )
    return out


def e2e_metrics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["split"], row["pipeline_name"])].append(row)
    out = []
    for (split, pipeline), group in sorted(grouped.items()):
        out.append(
            {
                "split": split,
                "pipeline_name": pipeline,
                "rows": len(group),
                "final_success_rate": _mean(group, "final_success"),
                "false_accept_rate": _mean(group, "false_accept"),
                "cost_to_correct": _cost_to_correct(group),
            }
        )
    return out


def _select_for_pipeline(
    pipeline: str,
    pool: list[dict[str, Any]],
    *,
    task_id: str,
) -> tuple[dict[str, Any], bool]:
    if pipeline == "single_sample":
        return pool[0], False
    selector_map = {
        "best_of_n_random": "random_selector",
        "best_of_n_tests_only": "tests_only_selector",
        "best_of_n_structural_only": "structural_selector",
        "best_of_n_llm_judge": "llm_judge_selector",
        "best_of_n_specoracle": "specoracle_selector",
        "best_of_n_specoracle_plus_one_repair": "specoracle_selector",
    }
    selected = SELECTORS[selector_map[pipeline]](pool, task_id=task_id)
    if pipeline.endswith("plus_one_repair") and selected["candidate_label"] != "correct":
        return repair_selected_candidate(selected), True
    return selected, False


def _group_by_task(
    candidate_rows: list[dict[str, Any]],
    *,
    split: str | None,
) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        if split and row["split"] != split:
            continue
        grouped[(row["surface"], row["split"], row["task_id"])].append(row)
    return {key: sorted(value, key=lambda row: row["candidate_id"]) for key, value in grouped.items()}


def _final_success(row: dict[str, Any]) -> bool:
    return bool(
        row.get("hidden_tests_pass")
        and row.get("property_checks_pass")
        and row.get("security_checks_pass")
        and row.get("regression_checks_pass")
    )


def _false_accept(row: dict[str, Any]) -> bool:
    return bool(row.get("visible_tests_pass")) and not _final_success(row)


def _secure_false_accept(row: dict[str, Any]) -> bool:
    return _false_accept(row) and not bool(row.get("security_checks_pass"))


def _regression_false_accept(row: dict[str, Any]) -> bool:
    return _false_accept(row) and not bool(row.get("regression_checks_pass"))


def _mean(rows: list[dict[str, Any]], key: str) -> float:
    if not rows:
        return 0.0
    return round(sum(1 for row in rows if row.get(key)) / len(rows), 6)


def _cost_to_correct(rows: list[dict[str, Any]]) -> float | None:
    successes = sum(1 for row in rows if row.get("final_success"))
    if successes == 0:
        return None
    return round(sum(float(row.get("cost_usd") or 0.0) for row in rows) / successes, 6)
