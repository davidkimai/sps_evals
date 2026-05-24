from __future__ import annotations

import json
import time
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from specoracle.vericoding.candidate_sources import (
    build_task_pool,
    split_manifest,
    surface_manifest,
)
from specoracle.vericoding.hidden_oracles import ensure_hidden_oracles, run_hidden_oracle
from specoracle.vericoding.live_generation import GENERATION_CONDITIONS, generate_live_candidate, repair_candidate_live
from specoracle.vericoding.live_selection import (
    observable_views,
    select_llm_judge_live,
    select_random_observable,
    select_specoracle_live,
    select_structural_observable,
    select_tests_only_observable,
)
from specoracle.vericoding.runtime_env import (
    RuntimeProvenance,
    assert_clean_or_sanctioned_run_root,
    preflight_report,
)
from specoracle.vericoding.schemas import (
    LIVE_DEFAULT_ROOT,
    LIVE_PROGRAM_VERSION,
    TaskQueueItem,
    VericodingPaths,
    append_jsonl,
    dataclass_to_dict,
    file_sha256,
    now_iso,
    read_jsonl,
    stable_hash,
    write_csv,
    write_json,
)

MODEL_DEFAULT = "gpt-5.4-mini"
LIVE_ROOT = LIVE_DEFAULT_ROOT
PHASE_BUDGETS = {
    "candidate_generation": 180.0,
    "selector_eval": 90.0,
    "e2e_confirmatory": 140.0,
    "secure_subset": 50.0,
    "external_guardrail": 80.0,
    "adjudication": 40.0,
}
HARD_CEILING = 580.0
LIVE_QUOTAS = {
    "internal": 120,
    "secure": 72,
    "scbench_regression": 32,
    "terminalbench_guardrail": 24,
}
PER_TASK_QUOTAS = {
    "internal": 6,
    "secure": 6,
    "scbench_regression": 4,
    "terminalbench_guardrail": 3,
}
WATCHDOG_MINUTES = {
    "live_candidate_bank": 20,
    "selector_dev": 15,
    "selector_confirmatory": 15,
    "e2e_confirmatory": 20,
    "external_guardrail": 30,
}
PIPELINES = (
    "single_sample",
    "best_of_n_random",
    "best_of_n_tests_only",
    "best_of_n_structural_only",
    "best_of_n_llm_judge",
    "best_of_n_specoracle",
    "best_of_n_specoracle_plus_one_repair",
)
SELECTORS = (
    "random_selector",
    "tests_only_selector",
    "structural_selector",
    "llm_judge_selector",
    "specoracle_selector",
)


def paths(root: Path = LIVE_ROOT) -> VericodingPaths:
    return VericodingPaths(root)


def preflight(*, root: Path = LIVE_ROOT, model: str = MODEL_DEFAULT, allow_dirty_live: bool = False) -> dict[str, Any]:
    p = paths(root)
    report = preflight_report(model=model, allow_dirty_live=allow_dirty_live)
    ensure_tree(p)
    ensure_hidden_oracles()
    write_json(p.state_dir / "program_state.json", _state("preflight", report=report))
    _write_report(
        p,
        "phase_00_preflight.md",
        "Preflight",
        [
            f"OpenAI key visible: `{report['openai_api_key_present']}`",
            f"Provider minimal request: `{report['provider_minimal_request']['ok']}`",
            f"Harbor available: `{report['harbor_available']}`",
            f"Inspect import available: `{report['inspect_import_available']}`",
            f"Runner dirty: `{report['runner_git_dirty']}`",
            f"Dirty override: `{allow_dirty_live}`",
            f"Child env path: `{report['child_env_path']}`",
        ],
    )
    return report


def bootstrap(*, root: Path = LIVE_ROOT) -> dict[str, Any]:
    p = paths(root)
    ensure_tree(p)
    task_pool = _v2_task_pool(build_task_pool())
    write_json(p.manifests_dir / "task_pool.json", task_pool)
    write_json(p.manifests_dir / "dev_manifest.json", split_manifest(task_pool, "dev"))
    write_json(p.manifests_dir / "confirmatory_manifest.json", split_manifest(task_pool, "confirmatory"))
    write_json(p.manifests_dir / "secure_subset_manifest.json", surface_manifest(task_pool, "secure"))
    write_json(
        p.manifests_dir / "terminalbench_guardrail_manifest.json",
        surface_manifest(task_pool, "terminalbench_guardrail"),
    )
    write_json(
        p.manifests_dir / "scbench_regression_manifest.json",
        _sanitize_scbench_manifest(surface_manifest(task_pool, "scbench_regression")),
    )
    _write_config(p)
    _write_eval_sets(p)
    _write_control_docs(p, task_pool)
    _initialize_queue(p, task_pool)
    previous = _read_state(p)
    state = _state("bootstrapped", report=previous.get("preflight", {}))
    state.update(_preserved_state_fields(previous))
    write_json(p.state_dir / "program_state.json", state)
    return task_pool


def run_all_live(
    *,
    root: Path = LIVE_ROOT,
    model: str = MODEL_DEFAULT,
    allow_dirty_live: bool = False,
    rehearsal_stop_after: int | None = None,
    resume_mode: bool = False,
) -> int:
    p = paths(root)
    state_before = _read_state(p)
    provenance_obj = assert_clean_or_sanctioned_run_root(
        run_root=root,
        allow_dirty_live=allow_dirty_live,
        state=state_before,
        resume=resume_mode,
    )
    provenance = provenance_obj.to_dict()
    started = time.monotonic()
    try:
        if resume_mode:
            _record_resume_acceptance(p, provenance_obj)
            task_pool = _load_task_pool(p)
        else:
            if not (state_before.get("preflight") and provenance_obj.sanctioned_dirty_run_root):
                preflight(root=root, model=model, allow_dirty_live=allow_dirty_live)
            task_pool = bootstrap(root=root)
            _record_clean_launch(p, provenance_obj, root=root)
        candidate_rows = live_candidate_bank(
            p,
            task_pool,
            model=model,
            provenance=provenance,
            rehearsal_stop_after=rehearsal_stop_after,
        )
        if rehearsal_stop_after is not None:
            _set_state(p, "rehearsal_interrupted", blockers=["deliberate_rehearsal_interrupt"])
            return 75
        selector_rows = selector_phase(p, candidate_rows, split="dev", model=model)
        selector_rows += selector_phase(p, candidate_rows, split="confirmatory", model=model)
        e2e_phase(p, candidate_rows, model=model, provenance=provenance)
        secure_phase(p, candidate_rows)
        external_guardrail_phase(p, candidate_rows)
        inspect_exports_phase(p)
        analyze(p, started_monotonic=started)
        export_paper(p)
        complete = _run_success_contract(p)
        _set_state(p, "complete" if complete else "downgraded_complete")
        return 0 if complete else 2
    except Exception as exc:
        _set_state(p, "stopped", blockers=[str(exc)])
        raise


def resume(
    *,
    root: Path = LIVE_ROOT,
    model: str = MODEL_DEFAULT,
    allow_dirty_live: bool = False,
    rehearsal_stop_after: int | None = None,
) -> int:
    # v2 resume is idempotent because ledgers are append-only and row IDs are stable.
    return run_all_live(
        root=root,
        model=model,
        allow_dirty_live=allow_dirty_live,
        rehearsal_stop_after=rehearsal_stop_after,
        resume_mode=True,
    )


def status(*, root: Path = LIVE_ROOT) -> dict[str, Any]:
    p = paths(root)
    state_path = p.state_dir / "program_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    return {
        "program_version": LIVE_PROGRAM_VERSION,
        "root": str(root),
        "state": state,
        "queue": _queue_counts(p),
        "candidate_rows": len(read_jsonl(p.ledgers_dir / "candidate_bank.jsonl")),
        "selector_rows": len(read_jsonl(p.ledgers_dir / "selector_eval.jsonl")),
        "e2e_rows": len(read_jsonl(p.ledgers_dir / "e2e_runs.jsonl")),
        "secure_rows": len(read_jsonl(p.ledgers_dir / "secure_eval.jsonl")),
    }


def _load_task_pool(p: VericodingPaths) -> dict[str, Any]:
    path = p.manifests_dir / "task_pool.json"
    if not path.exists():
        raise RuntimeError("resume requested before task_pool.json exists")
    return json.loads(path.read_text(encoding="utf-8"))


def _record_clean_launch(p: VericodingPaths, provenance: RuntimeProvenance, *, root: Path) -> None:
    state = _read_state(p)
    preflight_state = state.get("preflight") or {}
    preflight_clean = bool(preflight_state) and not bool(preflight_state.get("runner_git_dirty"))
    clean_launch = (not provenance.runner_git_dirty or preflight_clean) and not provenance.dirty_override
    state.update(
        {
            "clean_launch": clean_launch,
            "launch_git_commit": preflight_state.get("runner_git_commit") or provenance.runner_git_commit,
            "launch_diff_fingerprint": preflight_state.get("diff_fingerprint") or provenance.diff_fingerprint,
            "run_root": str(root),
            "launch_dirty_override": provenance.dirty_override,
            "launch_sanctioned_dirty_run_root": provenance.sanctioned_dirty_run_root,
            "launch_sanctioned_dirty_paths": list(provenance.sanctioned_dirty_paths),
        }
    )
    write_json(p.state_dir / "program_state.json", state)


def _record_resume_acceptance(p: VericodingPaths, provenance: RuntimeProvenance) -> None:
    state = _read_state(p)
    state.update(
        {
            "last_resume": {
                "created_at": now_iso(),
                "sanctioned_dirty_run_root": provenance.sanctioned_dirty_run_root,
                "sanctioned_dirty_paths": list(provenance.sanctioned_dirty_paths),
                "dirty_override": provenance.dirty_override,
                "run_root": provenance.run_root,
            }
        }
    )
    write_json(p.state_dir / "program_state.json", state)
    _write_report(
        p,
        "phase_resume.md",
        "Resume Acceptance",
        [
            f"Sanctioned run-root dirtiness: `{provenance.sanctioned_dirty_run_root}`",
            f"Sanctioned dirty path count: `{len(provenance.sanctioned_dirty_paths)}`",
            "No non-run-root dirty paths were accepted.",
        ],
    )


def live_candidate_bank(
    p: VericodingPaths,
    task_pool: dict[str, Any],
    *,
    model: str,
    provenance: dict[str, Any],
    rehearsal_stop_after: int | None = None,
) -> list[dict[str, Any]]:
    _watchdog_reconcile(p, "live_candidate_bank")
    existing = read_jsonl(p.ledgers_dir / "candidate_bank.jsonl")
    existing_ids = {row["bank_row_id"] for row in existing}
    emitted = 0
    for task in task_pool["tasks"]:
        conditions = list(GENERATION_CONDITIONS[task["surface"]])
        quota = PER_TASK_QUOTAS[task["surface"]]
        for sample_index in range(quota):
            condition = conditions[sample_index % len(conditions)]
            row_id = stable_hash(
                {
                    "program_version": LIVE_PROGRAM_VERSION,
                    "task_id": task["task_id"],
                    "condition": condition,
                    "sample_index": sample_index,
                },
                length=18,
            )
            if row_id in existing_ids:
                continue
            _mark_queue_running(p, task, "live_candidate_bank", condition)
            row = generate_live_candidate(
                task,
                condition=condition,
                sample_index=sample_index,
                model=model,
                artifact_dir=p.wrangled_dir / "live_candidates",
                provenance=provenance,
            )
            _validate_live_candidate_row(row)
            _append_unique(p.ledgers_dir / "candidate_bank.jsonl", [row], "bank_row_id")
            _mark_queue_completed(p, task, "live_candidate_bank", condition, rows=1, artifacts=1)
            emitted += 1
            _heartbeat(p, "live_candidate_bank")
            _enforce_phase_budget(p, "candidate_generation")
            if rehearsal_stop_after is not None and emitted >= rehearsal_stop_after:
                return read_jsonl(p.ledgers_dir / "candidate_bank.jsonl")
    rows = read_jsonl(p.ledgers_dir / "candidate_bank.jsonl")
    write_csv(p.wrangled_dir / "candidate_summary.csv", _candidate_summary(rows))
    _write_report(
        p,
        "phase_03_live_candidate_bank.md",
        "Live Candidate Bank",
        [
            f"Live rows: `{len([r for r in rows if r.get('candidate_source_type') == 'live_model'])}`",
            f"Surface quotas met: `{_surface_quotas_met(rows)}`",
            "Rows with zero provider evidence are excluded from primary evidence.",
        ],
    )
    return rows


def selector_phase(
    p: VericodingPaths,
    candidate_rows: list[dict[str, Any]],
    *,
    split: str,
    model: str,
) -> list[dict[str, Any]]:
    _watchdog_reconcile(p, f"selector_{split}")
    rows = []
    for key, pool in _group_candidates(candidate_rows, split=split).items():
        surface, task_id = key
        views = observable_views(pool)
        task_summary = f"{surface} task {task_id}; raw external content is not committed."
        for selector_name in SELECTORS:
            row_id = stable_hash(
                {
                    "program_version": LIVE_PROGRAM_VERSION,
                    "split": split,
                    "task_id": task_id,
                    "selector": selector_name,
                },
                length=18,
            )
            if _ledger_has(p.ledgers_dir / "selector_eval.jsonl", "selector_eval_row_id", row_id):
                continue
            _mark_simple_queue(p, surface, split, task_id, f"selector_{split}", selector_name, "running")
            if selector_name == "random_selector":
                chosen = select_random_observable(views, task_id=task_id)
                meta = _zero_selector_meta(selector_name)
            elif selector_name == "tests_only_selector":
                chosen = select_tests_only_observable(views)
                meta = _zero_selector_meta(selector_name)
            elif selector_name == "structural_selector":
                chosen = select_structural_observable(views)
                meta = _zero_selector_meta(selector_name)
            elif selector_name == "llm_judge_selector":
                chosen, meta = select_llm_judge_live(views, task_summary=task_summary, model=model)
            else:
                chosen, meta = select_specoracle_live(views, task_summary=task_summary, model=model)
            hidden = next(row for row in pool if row["candidate_id"] == chosen.candidate_id)
            out = _selector_row(
                row_id=row_id,
                surface=surface,
                split=split,
                task_id=task_id,
                selector_name=selector_name,
                selected=hidden,
                candidate_pool_size=len(pool),
                meta=meta,
            )
            _append_unique(p.ledgers_dir / "selector_eval.jsonl", [out], "selector_eval_row_id")
            rows.append(out)
            _mark_simple_queue(p, surface, split, task_id, f"selector_{split}", selector_name, "completed")
            _heartbeat(p, f"selector_{split}")
            _enforce_phase_budget(p, "selector_eval")
    all_rows = read_jsonl(p.ledgers_dir / "selector_eval.jsonl")
    write_csv(p.wrangled_dir / "selector_summary.csv", all_rows)
    write_csv(p.metrics_dir / "selector_metrics.csv", _selector_metrics(all_rows))
    _write_report(
        p,
        "phase_04_selector_dev.md" if split == "dev" else "phase_05_selector_confirmatory.md",
        "Selector Dev" if split == "dev" else "Selector Confirmatory",
        [f"Selector rows for `{split}` complete.", "Provider-backed selectors record nonzero cost/tokens."],
    )
    return rows


def e2e_phase(
    p: VericodingPaths,
    candidate_rows: list[dict[str, Any]],
    *,
    model: str,
    provenance: dict[str, Any],
) -> list[dict[str, Any]]:
    _watchdog_reconcile(p, "e2e_confirmatory")
    rows = []
    repair_attempts = 0
    for key, pool in _group_candidates(candidate_rows, split="confirmatory").items():
        surface, task_id = key
        task = _task_by_id(task_id)
        n = 3 if surface == "terminalbench_guardrail" else 4
        pool_n = pool[:n]
        views = observable_views(pool_n)
        for pipeline in PIPELINES:
            row_id = stable_hash(
                {
                    "program_version": LIVE_PROGRAM_VERSION,
                    "task_id": task_id,
                    "pipeline": pipeline,
                },
                length=18,
            )
            if _ledger_has(p.ledgers_dir / "e2e_runs.jsonl", "e2e_row_id", row_id):
                continue
            selected = _select_for_pipeline(pipeline, views, pool_n, task_id=task_id, model=model)
            repair_applied = False
            repair_cost = 0.0
            repair_tokens = {"input": 0, "output": 0}
            if pipeline == "best_of_n_specoracle_plus_one_repair" and repair_attempts < 12:
                repaired, repair_row = repair_candidate_live(
                    selected,
                    task=task,
                    model=model,
                    repair_dir=p.wrangled_dir / "repairs",
                    provenance=provenance,
                )
                _append_unique(p.ledgers_dir / "adjudications.jsonl", [repair_row], "adjudication_row_id")
                selected = repaired
                repair_applied = True
                repair_attempts += 1
                repair_cost = float(repair_row["incremental_cost_usd"])
                repair_tokens = {
                    "input": int(repair_row["input_tokens"]),
                    "output": int(repair_row["output_tokens"]),
                }
            out = {
                "e2e_row_id": row_id,
                "program_version": LIVE_PROGRAM_VERSION,
                "surface": surface,
                "split": "confirmatory",
                "task_id": task_id,
                "pipeline_name": pipeline,
                "n_candidates": len(pool_n),
                "selected_candidate_id": selected["candidate_id"],
                "repair_applied": repair_applied,
                "final_visible_tests_pass": bool(selected["visible_tests_pass"]),
                "final_hidden_tests_pass": bool(selected["hidden_tests_pass"]),
                "final_security_checks_pass": bool(selected["security_checks_pass"]),
                "final_regression_checks_pass": bool(selected["regression_checks_pass"]),
                "final_success": _final_success(selected),
                "false_accept": _false_accept(selected),
                "cost_usd": float(selected.get("cost_usd") or 0.0) + repair_cost,
                "input_tokens": int(selected.get("input_tokens") or 0) + repair_tokens["input"],
                "output_tokens": int(selected.get("output_tokens") or 0) + repair_tokens["output"],
                "wall_seconds": float(selected.get("wall_seconds") or 0.0),
                "created_at": now_iso(),
            }
            _append_unique(p.ledgers_dir / "e2e_runs.jsonl", [out], "e2e_row_id")
            rows.append(out)
            _heartbeat(p, "e2e_confirmatory")
            _enforce_phase_budget(p, "e2e_confirmatory")
    all_rows = read_jsonl(p.ledgers_dir / "e2e_runs.jsonl")
    write_csv(p.wrangled_dir / "e2e_summary.csv", all_rows)
    write_csv(p.metrics_dir / "e2e_metrics.csv", _e2e_metrics(all_rows))
    _write_report(
        p,
        "phase_06_e2e_confirmatory.md",
        "E2E Confirmatory",
        [f"E2E rows: `{len(all_rows)}`", f"Repair attempts: `{repair_attempts}`"],
    )
    return rows


def secure_phase(p: VericodingPaths, candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in candidate_rows:
        if row["surface"] != "secure" or row["split"] != "confirmatory":
            continue
        code = Path(row["candidate_artifact_path"]).read_text(encoding="utf-8")
        secure = run_hidden_oracle(row["task_id"], code)
        secure.update(
            {
                "program_version": LIVE_PROGRAM_VERSION,
                "candidate_id": row["candidate_id"],
                "candidate_sha256": row["candidate_sha256"],
            }
        )
        _append_unique(p.ledgers_dir / "secure_eval.jsonl", [secure], "secure_eval_row_id")
        rows.append(secure)
    all_rows = read_jsonl(p.ledgers_dir / "secure_eval.jsonl")
    write_csv(p.wrangled_dir / "secure_summary.csv", all_rows)
    write_csv(p.metrics_dir / "secure_metrics.csv", _secure_metrics(all_rows))
    _write_report(
        p,
        "phase_07_secure_subset.md",
        "Secure Subset",
        [f"Executable hidden-oracle rows: `{len(all_rows)}`"],
    )
    return rows


def external_guardrail_phase(p: VericodingPaths, candidate_rows: list[dict[str, Any]]) -> None:
    _watchdog_reconcile(p, "external_guardrail")
    rows = [row for row in candidate_rows if row["surface"] == "terminalbench_guardrail"]
    _write_report(
        p,
        "phase_08_external_guardrail.md",
        "External Guardrail",
        [
            f"Terminal guardrail live candidate/equivalent rows: `{len(rows)}`",
            "Raw Harbor jobs remain quarantined under ignored storage if run.",
        ],
    )


def inspect_exports_phase(p: VericodingPaths) -> None:
    _write_report(
        p,
        "phase_09_inspect_exports.md",
        "Inspect Exports",
        [
            "Vericoding Inspect tasks load sanitized manifests and derived summaries.",
            "Inspect execution is a materialization layer, not a substitute for live evidence.",
        ],
    )


def analyze(p: VericodingPaths, *, started_monotonic: float | None = None) -> dict[str, Any]:
    candidates = read_jsonl(p.ledgers_dir / "candidate_bank.jsonl")
    selectors = read_jsonl(p.ledgers_dir / "selector_eval.jsonl")
    e2e = read_jsonl(p.ledgers_dir / "e2e_runs.jsonl")
    secure = read_jsonl(p.ledgers_dir / "secure_eval.jsonl")
    adjudications = read_jsonl(p.ledgers_dir / "adjudications.jsonl")
    write_csv(p.wrangled_dir / "surface_summary.csv", _surface_summary(candidates, selectors, e2e))
    write_csv(p.wrangled_dir / "failure_taxonomy.csv", _failure_taxonomy(candidates))
    write_csv(p.metrics_dir / "budget_summary.csv", _budget_summary(candidates, selectors, e2e, adjudications))
    floors = _empirical_floors(candidates, selectors, e2e, secure, adjudications, started_monotonic)
    selector_metrics = _selector_metrics(selectors)
    e2e_metrics = _e2e_metrics(e2e)
    claims = _claim_status(floors, selector_metrics, e2e_metrics, secure)
    write_json(p.reports_dir / "claim_status.json", {"floors": floors, "claims": claims})
    _write_claims(p, claims)
    _write_final_synthesis(p, floors, claims)
    return {"floors": floors, "claims": claims}


def export_paper(p: VericodingPaths = paths()) -> None:
    for rel in ("paper_artifacts/tables", "paper_artifacts/figures", "paper_artifacts/appendix_cases"):
        (p.root / rel).mkdir(parents=True, exist_ok=True)
    for source, dest in (
        (p.manifests_dir / "task_pool.json", p.paper_dir / "tables/task_inventory.json"),
        (p.metrics_dir / "selector_metrics.csv", p.paper_dir / "tables/selector_metrics.csv"),
        (p.metrics_dir / "e2e_metrics.csv", p.paper_dir / "tables/e2e_metrics.csv"),
        (p.metrics_dir / "secure_metrics.csv", p.paper_dir / "tables/secure_metrics.csv"),
        (p.wrangled_dir / "surface_summary.csv", p.paper_dir / "tables/surface_summary.csv"),
    ):
        if source.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    (p.paper_dir / "figures/system_architecture.md").write_text(
        "# System Architecture\n\nInspect-native control plane with provider-backed generation, selection, repair, and sandbox/Harbor backends.\n",
        encoding="utf-8",
    )


def ensure_tree(p: VericodingPaths) -> None:
    for rel in (
        "config",
        "manifests/inspect_eval_sets",
        "ledgers",
        "data/raw",
        "data/wrangled/live_candidates",
        "data/wrangled/repairs",
        "metrics",
        "reports",
        "paper_artifacts/tables",
        "paper_artifacts/figures",
        "paper_artifacts/appendix_cases",
        "logs/inspect",
        "state",
        "raw_jobs",
    ):
        (p.root / rel).mkdir(parents=True, exist_ok=True)
    for name in ("candidate_bank.jsonl", "selector_eval.jsonl", "e2e_runs.jsonl", "secure_eval.jsonl", "adjudications.jsonl"):
        (p.ledgers_dir / name).touch(exist_ok=True)


def _v2_task_pool(task_pool: dict[str, Any]) -> dict[str, Any]:
    tasks = []
    for task in task_pool["tasks"]:
        updated = dict(task)
        updated["program_version"] = LIVE_PROGRAM_VERSION
        tasks.append(updated)
    out = dict(task_pool)
    out["program_version"] = LIVE_PROGRAM_VERSION
    out["schema_version"] = "vericoding_depth_v2_task_pool_v1"
    out["tasks"] = tasks
    out["manifest_sha256"] = stable_hash({k: v for k, v in out.items() if k != "manifest_sha256"})
    return out


def _sanitize_scbench_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    construction_script = Path("scripts/build_scbench_regression_manifest_v2.py")
    return {
        **manifest,
        "schema_version": "vericoding_depth_v2_scbench_sanitized_manifest_v1",
        "episode_construction": "derived_from_sprint9_external_subset_manifest_ids_hashes_only",
        "episode_construction_script": str(construction_script),
        "episode_construction_script_sha256": file_sha256(construction_script) if construction_script.exists() else "",
        "raw_content_committed": False,
        "tasks": [
            {
                key: task[key]
                for key in (
                    "program_version",
                    "surface",
                    "split",
                    "task_id",
                    "stable_sample_id",
                    "source_ref",
                    "task_hash",
                    "raw_content_committed",
                    "regression_sensitive",
                )
                if key in task
            }
            for task in manifest.get("tasks", [])
        ],
    }


def _write_config(p: VericodingPaths) -> None:
    write_json(
        p.config_dir / "params.json",
        {
            "program_version": LIVE_PROGRAM_VERSION,
            "default_model": MODEL_DEFAULT,
            "live_quotas": LIVE_QUOTAS,
            "per_task_quotas": PER_TASK_QUOTAS,
            "program_floors": {
                "candidate_rows": 248,
                "provider_spend_usd": 30.0,
                "input_tokens": 1_500_000,
                "output_tokens": 150_000,
                "repair_attempts": 12,
            },
            "raw_content_committed": False,
        },
    )
    write_json(p.config_dir / "budget_policy.json", {"phase_budgets": PHASE_BUDGETS, "hard_ceiling": HARD_CEILING})


def _write_eval_sets(p: VericodingPaths) -> None:
    for name in (
        "candidate_bank_dev",
        "candidate_bank_confirmatory",
        "selector_confirmatory",
        "e2e_confirmatory",
        "secure_confirmatory",
        "external_guardrail",
    ):
        (p.manifests_dir / "inspect_eval_sets" / f"{name}.yaml").write_text(
            f"program_version: {LIVE_PROGRAM_VERSION}\neval_set: {name}\nroot: runs/vericoding_depth_v2\nraw_content_committed: false\n",
            encoding="utf-8",
        )


def _write_control_docs(p: VericodingPaths, task_pool: dict[str, Any]) -> None:
    (p.root / "AGENTS.md").write_text(
        "# Vericoding Depth v2 Agent Contract\n\nMission: run provider-backed vericoding evidence.\n\nAnti-simulation: no deterministic fixture rows, hidden-label selectors, synthetic repair promotion, placeholder hidden oracles, or zero-cost ledgers can support claims.\n\nStop rules: dirty tree without override, leakage, budget exhaustion, selector hidden-field access, repair without artifact/reevaluation, or state/ledger divergence.\n",
        encoding="utf-8",
    )
    (p.root / "SPEC.md").write_text(
        "# Vericoding Depth v2 Spec\n\nInspect is the control plane. Ledgers are canonical scientific truth. Raw external benchmark content and hidden oracles remain ignored.\n",
        encoding="utf-8",
    )
    (p.root / "CLAIMS.md").write_text(
        "# Vericoding Depth v2 Claims\n\nClaims are unadjudicated until live ledgers are analyzed.\n",
        encoding="utf-8",
    )
    (p.root / "TASK_REGISTRY.md").write_text(
        f"# Task Registry\n\nTotal tasks: `{task_pool['actual_count']}`\n",
        encoding="utf-8",
    )
    _write_report(p, "phase_01_foundation.md", "Foundation", ["v2 live package initialized."])
    _write_report(p, "phase_02_task_pool.md", "Task Pool", [f"Tasks: `{task_pool['actual_count']}`"])


def _initialize_queue(p: VericodingPaths, task_pool: dict[str, Any]) -> None:
    path = p.state_dir / "task_queue.json"
    if path.exists():
        return
    items = []
    for task in task_pool["tasks"]:
        for sample_index in range(PER_TASK_QUOTAS[task["surface"]]):
            condition = GENERATION_CONDITIONS[task["surface"]][sample_index % len(GENERATION_CONDITIONS[task["surface"]])]
            items.append(_queue_item(task, "live_candidate_bank", condition))
    write_json(path, {"program_version": LIVE_PROGRAM_VERSION, "items": items})


def _queue_item(task: dict[str, Any], phase: str, condition: str) -> dict[str, Any]:
    now = now_iso()
    return dataclass_to_dict(
        TaskQueueItem(
            work_item_id=stable_hash({"phase": phase, "task": task["task_id"], "condition": condition}, length=18),
            surface=task["surface"],
            split=task["split"],
            task_id=task["task_id"],
            condition_or_pipeline=condition,
            phase=phase,
            status="pending",
            retry_index=0,
            last_progress_at=now,
            started_at="",
            completed_at="",
            stop_reason="",
            ledger_rows_emitted=0,
            artifact_count=0,
        )
    )


def _mark_queue_running(p: VericodingPaths, task: dict[str, Any], phase: str, condition: str) -> None:
    _update_queue_item(p, task["task_id"], phase, condition, status="running", started_at=now_iso())


def _mark_queue_completed(
    p: VericodingPaths,
    task: dict[str, Any],
    phase: str,
    condition: str,
    *,
    rows: int,
    artifacts: int,
) -> None:
    _update_queue_item(
        p,
        task["task_id"],
        phase,
        condition,
        status="completed",
        completed_at=now_iso(),
        ledger_rows_emitted=rows,
        artifact_count=artifacts,
    )


def _mark_simple_queue(
    p: VericodingPaths,
    surface: str,
    split: str,
    task_id: str,
    phase: str,
    condition: str,
    status: str,
) -> None:
    queue_path = p.state_dir / "task_queue.json"
    queue = json.loads(queue_path.read_text(encoding="utf-8")) if queue_path.exists() else {"items": []}
    item_id = stable_hash({"phase": phase, "task": task_id, "condition": condition}, length=18)
    item = next((item for item in queue["items"] if item["work_item_id"] == item_id), None)
    if item is None:
        item = _queue_item(
            {"surface": surface, "split": split, "task_id": task_id},
            phase,
            condition,
        )
        queue["items"].append(item)
    item["status"] = status
    item["last_progress_at"] = now_iso()
    if status == "running":
        item["started_at"] = item["started_at"] or now_iso()
    if status == "completed":
        item["completed_at"] = now_iso()
        item["ledger_rows_emitted"] = 1
    write_json(queue_path, queue)


def _watchdog_reconcile(
    p: VericodingPaths,
    phase: str,
    *,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    queue_path = p.state_dir / "task_queue.json"
    if not queue_path.exists():
        return []
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    threshold = timedelta(minutes=WATCHDOG_MINUTES.get(phase, 20))
    current = now or datetime.now(UTC)
    stalled: list[dict[str, Any]] = []
    for item in queue.get("items", []):
        if item.get("phase") != phase or item.get("status") != "running":
            continue
        last_progress = _parse_iso(item.get("last_progress_at") or item.get("started_at") or now_iso())
        if current - last_progress <= threshold:
            continue
        item["retry_index"] = int(item.get("retry_index") or 0) + 1
        item["last_progress_at"] = now_iso()
        if item["retry_index"] == 1:
            item["status"] = "pending"
            item["stop_reason"] = "watchdog_stall_targeted_retry"
        else:
            item["status"] = "downgraded"
            item["stop_reason"] = "watchdog_repeated_stall"
        stalled.append(dict(item))
    if stalled:
        write_json(queue_path, queue)
        _set_state(
            p,
            f"{phase}_watchdog_reconciled",
            blockers=[f"{len(stalled)} stalled work item(s) reconciled"],
        )
    return stalled


def _update_queue_item(p: VericodingPaths, task_id: str, phase: str, condition: str, **updates: Any) -> None:
    queue_path = p.state_dir / "task_queue.json"
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    item_id = stable_hash({"phase": phase, "task": task_id, "condition": condition}, length=18)
    for item in queue["items"]:
        if item["work_item_id"] == item_id:
            item.update(updates)
            item["last_progress_at"] = now_iso()
            break
    write_json(queue_path, queue)


def _heartbeat(p: VericodingPaths, phase: str) -> None:
    current = {}
    state_path = p.state_dir / "program_state.json"
    if state_path.exists():
        current = json.loads(state_path.read_text(encoding="utf-8"))
    current.update(_state(phase, report=current.get("preflight", {})))
    write_json(state_path, current)


def _state(phase: str, *, report: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "program_version": LIVE_PROGRAM_VERSION,
        "current_phase": phase,
        "phase_status": phase,
        "manifests_frozen": phase not in {"preflight"},
        "selector_semantics_frozen": phase
        in {"selector_confirmatory", "e2e_confirmatory", "complete", "downgraded_complete"},
        "budget_used": 0.0,
        "live_rows_completed": 0,
        "provider_calls_completed": 0,
        "harbor_jobs_completed": 0,
        "last_heartbeat_at": now_iso(),
        "last_successful_command": phase,
        "next_required_action": phase,
        "blockers": [],
        "preflight": report or {},
    }


def _set_state(p: VericodingPaths, phase: str, *, blockers: list[str] | None = None) -> None:
    previous = _read_state(p)
    state = _state(phase, report=previous.get("preflight", {}))
    state.update(_preserved_state_fields(previous))
    state["blockers"] = blockers or []
    write_json(p.state_dir / "program_state.json", state)


def _preserved_state_fields(state: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "clean_launch",
        "launch_git_commit",
        "launch_diff_fingerprint",
        "run_root",
        "launch_dirty_override",
        "launch_sanctioned_dirty_run_root",
        "launch_sanctioned_dirty_paths",
        "last_resume",
    )
    return {key: state[key] for key in keys if key in state}


def _read_state(p: VericodingPaths) -> dict[str, Any]:
    state_path = p.state_dir / "program_state.json"
    if not state_path.exists():
        return {}
    return json.loads(state_path.read_text(encoding="utf-8"))


def _write_report(p: VericodingPaths, filename: str, title: str, bullets: list[str]) -> None:
    body = [f"# {title}", ""]
    body.extend(f"- {item}" for item in bullets)
    (p.reports_dir / filename).write_text("\n".join(body) + "\n", encoding="utf-8")


def _append_unique(path: Path, rows: list[dict[str, Any]], id_key: str) -> None:
    existing = read_jsonl(path)
    ids = {row[id_key] for row in existing}
    append_jsonl(path, [row for row in rows if row[id_key] not in ids])


def _ledger_has(path: Path, id_key: str, row_id: str) -> bool:
    return any(row.get(id_key) == row_id for row in read_jsonl(path))


def _validate_live_candidate_row(row: dict[str, Any]) -> None:
    if row.get("candidate_source_type") == "live_model":
        if float(row.get("cost_usd") or 0) <= 0:
            raise RuntimeError("live_model candidate row has zero cost")
        if int(row.get("input_tokens") or 0) <= 0 or int(row.get("output_tokens") or 0) <= 0:
            raise RuntimeError("live_model candidate row has zero tokens")
        if float(row.get("wall_seconds") or 0) <= 0:
            raise RuntimeError("live_model candidate row has zero wall time")


def _group_candidates(candidate_rows: list[dict[str, Any]], *, split: str) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        if row["split"] == split:
            grouped[(row["surface"], row["task_id"])].append(row)
    return {key: sorted(value, key=lambda row: row["candidate_id"]) for key, value in grouped.items()}


def _zero_selector_meta(selector_name: str) -> dict[str, Any]:
    return {
        "selector_name": selector_name,
        "selector_cost_usd": 0.0,
        "selector_input_tokens": 0,
        "selector_output_tokens": 0,
        "selector_wall_seconds": 0.0,
        "selector_prompt_version": "observable_baseline_v2",
        "comparison_count": 0,
    }


def _selector_row(
    *,
    row_id: str,
    surface: str,
    split: str,
    task_id: str,
    selector_name: str,
    selected: dict[str, Any],
    candidate_pool_size: int,
    meta: dict[str, Any],
) -> dict[str, Any]:
    return {
        "selector_eval_row_id": row_id,
        "program_version": LIVE_PROGRAM_VERSION,
        "surface": surface,
        "split": split,
        "task_id": task_id,
        "selector_name": selector_name,
        "candidate_pool_size": candidate_pool_size,
        "selected_candidate_id": selected["candidate_id"],
        "selected_label": selected["candidate_label"],
        "selected_visible_tests_pass": bool(selected["visible_tests_pass"]),
        "selected_hidden_tests_pass": bool(selected["hidden_tests_pass"]),
        "selected_security_checks_pass": bool(selected["security_checks_pass"]),
        "selected_regression_checks_pass": bool(selected["regression_checks_pass"]),
        "selection_correct": selected["candidate_label"] == "correct",
        "false_accept": _false_accept(selected),
        "secure_false_accept": _false_accept(selected) and not bool(selected["security_checks_pass"]),
        "regression_false_accept": _false_accept(selected) and not bool(selected["regression_checks_pass"]),
        "selector_cost_usd": meta["selector_cost_usd"],
        "selector_input_tokens": meta["selector_input_tokens"],
        "selector_output_tokens": meta["selector_output_tokens"],
        "selector_wall_seconds": meta["selector_wall_seconds"],
        "selector_prompt_version": meta.get("selector_prompt_version", ""),
        "comparison_count": meta["comparison_count"],
        "created_at": now_iso(),
    }


def _select_for_pipeline(
    pipeline: str,
    views: list[Any],
    pool: list[dict[str, Any]],
    *,
    task_id: str,
    model: str,
) -> dict[str, Any]:
    if pipeline == "single_sample":
        chosen = views[0]
    elif pipeline == "best_of_n_random":
        chosen = select_random_observable(views, task_id=task_id)
    elif pipeline == "best_of_n_tests_only":
        chosen = select_tests_only_observable(views)
    elif pipeline == "best_of_n_structural_only":
        chosen = select_structural_observable(views)
    elif pipeline == "best_of_n_llm_judge":
        chosen, _meta = select_llm_judge_live(views, task_summary=task_id, model=model)
    else:
        chosen, _meta = select_specoracle_live(views, task_summary=task_id, model=model)
    return next(row for row in pool if row["candidate_id"] == chosen.candidate_id)


def _task_by_id(task_id: str) -> dict[str, Any]:
    for task in _v2_task_pool(build_task_pool())["tasks"]:
        if task["task_id"] == task_id:
            return task
    raise KeyError(task_id)


def _candidate_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["surface"], row["split"])
        item = grouped.setdefault(key, {"surface": row["surface"], "split": row["split"], "rows": 0, "live_model_rows": 0})
        item["rows"] += 1
        if row.get("candidate_source_type") == "live_model":
            item["live_model_rows"] += 1
    return list(grouped.values())


def _selector_metrics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["split"], row["selector_name"])].append(row)
    return [
        {
            "split": split,
            "selector_name": selector,
            "rows": len(group),
            "top1_accuracy": _rate(group, "selection_correct"),
            "false_accept_rate": _rate(group, "false_accept"),
            "secure_false_accept_rate": _rate(group, "secure_false_accept"),
            "regression_false_accept_rate": _rate(group, "regression_false_accept"),
        }
        for (split, selector), group in sorted(grouped.items())
    ]


def _e2e_metrics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["split"], row["pipeline_name"])].append(row)
    return [
        {
            "split": split,
            "pipeline_name": pipeline,
            "rows": len(group),
            "final_success_rate": _rate(group, "final_success"),
            "false_accept_rate": _rate(group, "false_accept"),
        }
        for (split, pipeline), group in sorted(grouped.items())
    ]


def _secure_metrics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "rows": len(rows),
            "hidden_oracle_execution_rate": _rate(rows, "hidden_oracle_executed"),
            "hidden_pass_rate": _rate(rows, "hidden_passed"),
        }
    ]


def _rate(rows: list[dict[str, Any]], key: str) -> float:
    return round(sum(1 for row in rows if row.get(key)) / len(rows), 6) if rows else 0.0


def _final_success(row: dict[str, Any]) -> bool:
    return bool(
        row.get("hidden_tests_pass")
        and row.get("property_checks_pass")
        and row.get("security_checks_pass")
        and row.get("regression_checks_pass")
    )


def _false_accept(row: dict[str, Any]) -> bool:
    return bool(row.get("visible_tests_pass")) and not _final_success(row)


def _surface_quotas_met(rows: list[dict[str, Any]]) -> bool:
    return all(
        sum(1 for row in rows if row["surface"] == surface and row.get("candidate_source_type") == "live_model") >= quota
        for surface, quota in LIVE_QUOTAS.items()
    )


def _empirical_floors(
    candidates: list[dict[str, Any]],
    selectors: list[dict[str, Any]],
    e2e: list[dict[str, Any]],
    secure: list[dict[str, Any]],
    adjudications: list[dict[str, Any]],
    started_monotonic: float | None,
) -> dict[str, Any]:
    live = [row for row in candidates if row.get("candidate_source_type") == "live_model"]
    confirmatory = [row for row in candidates if row["split"] == "confirmatory"]
    confirmatory_live = [row for row in confirmatory if row.get("candidate_source_type") == "live_model"]
    total_spend = sum(float(row.get("cost_usd") or 0) for row in candidates)
    total_spend += sum(float(row.get("selector_cost_usd") or 0) for row in selectors)
    total_spend += sum(float(row.get("cost_usd") or 0) for row in e2e)
    total_spend += sum(float(row.get("incremental_cost_usd") or 0) for row in adjudications)
    input_tokens = sum(int(row.get("input_tokens") or 0) for row in candidates)
    input_tokens += sum(int(row.get("selector_input_tokens") or 0) for row in selectors)
    input_tokens += sum(int(row.get("input_tokens") or 0) for row in e2e)
    input_tokens += sum(int(row.get("input_tokens") or 0) for row in adjudications)
    output_tokens = sum(int(row.get("output_tokens") or 0) for row in candidates)
    output_tokens += sum(int(row.get("selector_output_tokens") or 0) for row in selectors)
    output_tokens += sum(int(row.get("output_tokens") or 0) for row in e2e)
    output_tokens += sum(int(row.get("output_tokens") or 0) for row in adjudications)
    runtime = round((time.monotonic() - started_monotonic) if started_monotonic else 0, 3)
    return {
        "live_candidate_rows": len(live),
        "surface_quotas_met": _surface_quotas_met(candidates),
        "confirmatory_live_ratio": round(len(confirmatory_live) / len(confirmatory), 6) if confirmatory else 0,
        "provider_spend_usd": round(total_spend, 6),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "supervised_wall_seconds": runtime,
        "repair_attempts": len(adjudications),
        "secure_hidden_oracles_completed": bool(secure) and all(row.get("hidden_oracle_executed") for row in secure),
        "program_floors_met": (
            len(live) >= 248
            and total_spend >= 30
            and input_tokens >= 1_500_000
            and output_tokens >= 150_000
            and len(adjudications) >= 12
            and bool(secure)
        ),
    }


def _claim_status(
    floors: dict[str, Any],
    selector_metrics: list[dict[str, Any]],
    e2e_metrics: list[dict[str, Any]],
    secure: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    spec = _metric(selector_metrics, "confirmatory", "specoracle_selector", "selector_name")
    tests = _metric(selector_metrics, "confirmatory", "tests_only_selector", "selector_name")
    structural = _metric(selector_metrics, "confirmatory", "structural_selector", "selector_name")
    spec_e2e = _metric(e2e_metrics, "confirmatory", "best_of_n_specoracle", "pipeline_name")
    single = _metric(e2e_metrics, "confirmatory", "single_sample", "pipeline_name")
    live_claim_floor = floors["program_floors_met"]
    return [
        {
            "claim_id": "Claim 1",
            "status": (
                "supported"
                if live_claim_floor
                and float(spec.get("top1_accuracy", 0)) > max(float(tests.get("top1_accuracy", 0)), float(structural.get("top1_accuracy", 0)))
                else "partial"
            ),
            "evidence": "metrics/selector_metrics.csv",
        },
        {
            "claim_id": "Claim 2",
            "status": (
                "supported"
                if live_claim_floor and float(spec_e2e.get("final_success_rate", 0)) > float(single.get("final_success_rate", 0))
                else "partial"
            ),
            "evidence": "metrics/e2e_metrics.csv",
        },
        {"claim_id": "Claim 3", "status": "partial", "evidence": "metrics/selector_metrics.csv"},
        {
            "claim_id": "Claim 4",
            "status": "supported" if live_claim_floor and floors["secure_hidden_oracles_completed"] else "unsupported",
            "evidence": "metrics/secure_metrics.csv",
        },
    ]


def _metric(rows: list[dict[str, Any]], split: str, name: str, name_key: str) -> dict[str, Any]:
    for row in rows:
        if row.get("split") == split and row.get(name_key) == name:
            return row
    return {}


def _surface_summary(candidates: list[dict[str, Any]], selectors: list[dict[str, Any]], e2e: list[dict[str, Any]]) -> list[dict[str, Any]]:
    surfaces = sorted({row["surface"] for row in candidates})
    return [
        {
            "surface": surface,
            "candidate_rows": sum(1 for row in candidates if row["surface"] == surface),
            "selector_rows": sum(1 for row in selectors if row["surface"] == surface),
            "e2e_rows": sum(1 for row in e2e if row["surface"] == surface),
        }
        for surface in surfaces
    ]


def _failure_taxonomy(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], int] = defaultdict(int)
    for row in candidates:
        grouped[(row["surface"], row["candidate_label"])] += 1
    return [{"surface": s, "candidate_label": label, "count": count} for (s, label), count in sorted(grouped.items())]


def _budget_summary(candidates: list[dict[str, Any]], selectors: list[dict[str, Any]], e2e: list[dict[str, Any]], adjudications: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"phase": "candidate_generation", "cost_usd": sum(float(row.get("cost_usd") or 0) for row in candidates)},
        {"phase": "selector_eval", "cost_usd": sum(float(row.get("selector_cost_usd") or 0) for row in selectors)},
        {"phase": "e2e_confirmatory", "cost_usd": sum(float(row.get("cost_usd") or 0) for row in e2e)},
        {"phase": "adjudication", "cost_usd": sum(float(row.get("incremental_cost_usd") or 0) for row in adjudications)},
    ]


def _enforce_phase_budget(p: VericodingPaths, phase: str) -> None:
    rows = read_jsonl(p.ledgers_dir / "candidate_bank.jsonl")
    selectors = read_jsonl(p.ledgers_dir / "selector_eval.jsonl")
    e2e = read_jsonl(p.ledgers_dir / "e2e_runs.jsonl")
    adjudications = read_jsonl(p.ledgers_dir / "adjudications.jsonl")
    spent = {row["phase"]: float(row["cost_usd"]) for row in _budget_summary(rows, selectors, e2e, adjudications)}
    if spent.get(phase, 0.0) > PHASE_BUDGETS[phase]:
        raise RuntimeError(f"phase budget exceeded for {phase}: {spent[phase]:.2f} > {PHASE_BUDGETS[phase]:.2f}")
    if sum(spent.values()) > HARD_CEILING:
        raise RuntimeError("hard budget ceiling exceeded")


def _run_success_contract(p: VericodingPaths) -> bool:
    required = [
        p.wrangled_dir / "candidate_summary.csv",
        p.wrangled_dir / "selector_summary.csv",
        p.wrangled_dir / "e2e_summary.csv",
        p.wrangled_dir / "secure_summary.csv",
        p.reports_dir / "final_synthesis.md",
        p.root / "CLAIMS.md",
    ]
    return all(path.exists() for path in required)


def _write_claims(p: VericodingPaths, claims: list[dict[str, Any]]) -> None:
    lines = ["# Vericoding Depth v2 Claims", ""]
    for claim in claims:
        lines.extend([f"## {claim['claim_id']}", "", f"- Status: `{claim['status']}`", f"- Evidence: `{claim['evidence']}`", ""])
    (p.root / "CLAIMS.md").write_text("\n".join(lines), encoding="utf-8")


def _write_final_synthesis(p: VericodingPaths, floors: dict[str, Any], claims: list[dict[str, Any]]) -> None:
    lines = [
        "# Vericoding Depth v2 Final Synthesis",
        "",
        "This synthesis is derived from live v2 ledgers only.",
        "",
        "## Empirical Floors",
        "",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in floors.items())
    lines.extend(["", "## Claims", ""])
    lines.extend(f"- {claim['claim_id']}: `{claim['status']}`" for claim in claims)
    (p.reports_dir / "final_synthesis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _queue_counts(p: VericodingPaths) -> dict[str, int]:
    path = p.state_dir / "task_queue.json"
    if not path.exists():
        return {}
    queue = json.loads(path.read_text(encoding="utf-8"))
    counts: dict[str, int] = defaultdict(int)
    for item in queue.get("items", []):
        counts[item["status"]] += 1
    return dict(counts)


def _parse_iso(value: str) -> datetime:
    if not value:
        return datetime.now(UTC)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(UTC)
