from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import UTC, datetime, timedelta
import json
import subprocess
import time
from pathlib import Path
from typing import Any

from specoracle.vericoding.candidate_sources import build_task_pool, split_manifest, surface_manifest
from specoracle.vericoding.hidden_oracles import ensure_hidden_oracles, run_hidden_oracle
from specoracle.vericoding.live_generation import generate_live_candidate, repair_candidate_live
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
    estimate_openai_cost,
    preflight_report,
)
from specoracle.vericoding.schemas import (
    TaskQueueItem,
    VericodingPaths,
    append_jsonl,
    dataclass_to_dict,
    now_iso,
    read_json,
    read_jsonl,
    stable_hash,
    write_csv,
    write_json,
)

RESEARCH_PROGRAM_VERSION = "vericoding_research_v2"
RESEARCH_DEFAULT_ROOT = Path("runs/vericoding_research_v2")
MODEL_DEFAULT = "gpt-5.4-mini"

RESEARCH_PHASE_BUDGETS = {
    "pilot": 3.0,
    "candidate_generation": 24.0,
    "selector_eval": 8.0,
    "e2e_repair": 10.0,
    "external_harbor": 8.0,
    "formal_slice": 2.0,
    "adjudication": 5.0,
}
RESEARCH_HARD_CEILING = 60.0
RESEARCH_REVIEW_THRESHOLD = 25.0
RESEARCH_EXPECTED_SPEND = {"low": 6.0, "high": 18.0}

RESEARCH_EMPIRICAL_FLOORS = {
    "live_model_candidate_rows": 600,
    "provider_or_harbor_spend_usd": 1.0,
    "input_tokens": 250_000,
    "output_tokens": 400_000,
    "supervised_runtime_seconds": 0,
    "repair_reevaluations": 20,
    "harbor_completed_external_rows": 6,
    "semi_formal_rows": 5,
}

PROMPT_TOKEN_LIMITS = {
    "generation_prompt": 6_000,
    "selector_prompt": 8_000,
    "repair_prompt": 8_000,
}

PROVIDER_SELECTOR_NAMES = {"llm_judge_selector", "specoracle_selector"}
PROVIDER_E2E_PIPELINES = {
    "best_of_n_llm_judge",
    "best_of_n_specoracle",
    "best_of_n_specoracle_plus_one_repair",
}
PRIMARY_SURFACES = {"internal", "secure"}
SECONDARY_SURFACES = {"scbench_regression"}
TERTIARY_SURFACES = {"terminalbench_guardrail"}
PRIMARY_CORE_TASK_TARGET = 32
SELECTORS = (
    "random_selector",
    "tests_only_selector",
    "structural_selector",
    "llm_judge_selector",
    "specoracle_selector",
)
PIPELINES = (
    "single_sample",
    "best_of_n_random",
    "best_of_n_tests_only",
    "best_of_n_structural_only",
    "best_of_n_llm_judge",
    "best_of_n_specoracle",
    "best_of_n_specoracle_plus_one_repair",
)
RESEARCH_PER_TASK_QUOTAS = {
    "internal": 12,
    "secure": 10,
    "scbench_regression": 12,
    "terminalbench_guardrail": 18,
}
RESEARCH_LIVE_QUOTAS = {
    "internal": 240,
    "secure": 120,
    "scbench_regression": 96,
    "terminalbench_guardrail": 144,
}
ORACLE_GENERATION_MODES = (
    "baseline",
    "zen_oracle",
    "karpathy_oracle",
    "hybrid_structural_gate",
    "baseline_plus_repair_seed",
    "zen_plus_repair_seed",
    "karpathy_plus_repair_seed",
)
POOL_REGIMES = (
    "iid_baseline_only",
    "iid_zen_only",
    "iid_karpathy_only",
    "mixed_baseline_zen",
    "mixed_baseline_karpathy",
    "mixed_zen_karpathy",
    "mixed_baseline_zen_karpathy",
    "mixed_plus_hybrid",
    "repair_seeded_near_miss",
)
GENERATION_MODE_POOL_REGIME = {
    "baseline": "iid_baseline_only",
    "zen_oracle": "iid_zen_only",
    "karpathy_oracle": "iid_karpathy_only",
    "hybrid_structural_gate": "mixed_plus_hybrid",
    "baseline_plus_repair_seed": "repair_seeded_near_miss",
    "zen_plus_repair_seed": "repair_seeded_near_miss",
    "karpathy_plus_repair_seed": "repair_seeded_near_miss",
}
WATCHDOG_MINUTES = {
    "pilot_live": 20,
    "live_candidate_bank": 20,
    "core_dev": 20,
    "core_confirmatory": 20,
    "selector_dev": 15,
    "selector_confirmatory": 15,
    "e2e_confirmatory": 20,
    "external_guardrail": 30,
}


def paths(root: Path = RESEARCH_DEFAULT_ROOT) -> VericodingPaths:
    return VericodingPaths(root)


def budget_policy() -> dict[str, Any]:
    policy = {
        "program_version": RESEARCH_PROGRAM_VERSION,
        "model_policy": {
            "default_model": MODEL_DEFAULT,
            "pricing_basis": "OpenAI standard short-context text pricing",
            "input_usd_per_1m": 0.75,
            "cached_input_usd_per_1m": 0.075,
            "output_usd_per_1m": 4.50,
            "long_context_allowed": False,
            "prompt_bloat_policy": "pause_for_reauthorization",
        },
        "phase_caps_usd": RESEARCH_PHASE_BUDGETS,
        "hard_ceiling_usd": RESEARCH_HARD_CEILING,
        "mandatory_review_threshold_usd": RESEARCH_REVIEW_THRESHOLD,
        "expected_spend_usd": RESEARCH_EXPECTED_SPEND,
        "empirical_floors": RESEARCH_EMPIRICAL_FLOORS,
        "prompt_token_limits": PROMPT_TOKEN_LIMITS,
    }
    validate_budget_policy(policy)
    return policy


def validate_budget_policy(policy: dict[str, Any]) -> None:
    phase_total = round(sum(float(value) for value in policy["phase_caps_usd"].values()), 6)
    hard_ceiling = float(policy["hard_ceiling_usd"])
    review_threshold = float(policy["mandatory_review_threshold_usd"])
    if phase_total != hard_ceiling:
        raise ValueError(f"phase caps sum to {phase_total}, expected hard ceiling {hard_ceiling}")
    if review_threshold >= hard_ceiling:
        raise ValueError("mandatory review threshold must be below the hard ceiling")


def enforce_phase_cap(phase: str, phase_spend_usd: float) -> None:
    cap = RESEARCH_PHASE_BUDGETS[phase]
    if phase_spend_usd > cap:
        raise RuntimeError(f"{phase} phase budget exceeded: {phase_spend_usd:.4f} > {cap:.4f}")


def spend_gate(total_spend_usd: float, *, claim_movement_visible: bool) -> dict[str, Any]:
    if total_spend_usd > RESEARCH_HARD_CEILING:
        raise RuntimeError(
            f"vericoding research v2 hard ceiling exceeded: {total_spend_usd:.4f} > {RESEARCH_HARD_CEILING:.4f}"
        )
    review_required = total_spend_usd >= RESEARCH_REVIEW_THRESHOLD and not claim_movement_visible
    return {
        "total_spend_usd": round(total_spend_usd, 6),
        "review_required": review_required,
        "stop_reason": f"mandatory_{RESEARCH_REVIEW_THRESHOLD:g}_usd_review_gate" if review_required else "",
    }


def prompt_budget_check(prompt_kind: str, estimated_tokens: int) -> dict[str, Any]:
    limit = PROMPT_TOKEN_LIMITS[prompt_kind]
    return {
        "prompt_kind": prompt_kind,
        "estimated_tokens": estimated_tokens,
        "limit": limit,
        "ok": estimated_tokens <= limit,
        "stop_reason": "" if estimated_tokens <= limit else "prompt_bloat_requires_reauthorization",
    }


def empirical_floor_status(evidence: dict[str, Any]) -> dict[str, Any]:
    checks = {
        key: _floor_met(key, evidence.get(key, 0), floor)
        for key, floor in RESEARCH_EMPIRICAL_FLOORS.items()
    }
    runtime_floor_met = bool(checks["supervised_runtime_seconds"]["met"])
    token_and_spend_met = bool(checks["input_tokens"]["met"] and checks["output_tokens"]["met"])
    if token_and_spend_met and checks["provider_or_harbor_spend_usd"]["met"]:
        checks["supervised_runtime_seconds"]["met"] = True
        checks["supervised_runtime_seconds"]["waived_by_token_spend_floor"] = True
    return {
        "program_floors_met": all(check["met"] for check in checks.values()),
        "runtime_floor_met_before_waiver": runtime_floor_met,
        "checks": checks,
    }


def claim_status_from_evidence(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    floors = empirical_floor_status(evidence)
    supported_allowed = bool(floors["program_floors_met"])
    claim_1_status = "supported" if supported_allowed and evidence.get("claim_1_oracle_support_headroom") else "partial"
    claim_2_status = "supported" if supported_allowed and evidence.get("claim_2_visible_hidden_disagreement") else "partial"
    claim_3_status = "supported" if supported_allowed and evidence.get("claim_3_ranking_support_mechanism") else "partial"
    claim_4_status = "supported" if supported_allowed and evidence.get("claim_4_secure_false_accept_reduced") else "unsupported"
    claim_5_status = "supported" if supported_allowed and evidence.get("claim_5_repair_uplift") else "partial"
    return [
        {
            "claim_id": "Claim 1",
            "status": claim_1_status,
            "floor_gated": not supported_allowed,
            "claim": "Oracle-diverse candidate banks create selector headroom.",
        },
        {
            "claim_id": "Claim 2",
            "status": claim_2_status,
            "floor_gated": not supported_allowed,
            "claim": "Hidden regression and secure properties reveal failures visible tests miss.",
        },
        {
            "claim_id": "Claim 3",
            "status": claim_3_status,
            "floor_gated": not supported_allowed,
            "claim": "Ranking helps on some surfaces and fails on others for support-driven reasons.",
        },
        {
            "claim_id": "Claim 4",
            "status": claim_4_status,
            "floor_gated": not supported_allowed,
            "claim": "The selector reduces false acceptance on secure/property tasks.",
        },
        {
            "claim_id": "Claim 5",
            "status": claim_5_status,
            "floor_gated": not supported_allowed,
            "claim": "One bounded repair is a secondary gain mechanism on near-miss candidates.",
        },
    ]


def recompute_v2_corrected_cost(root: Path = Path("runs/vericoding_depth_v2")) -> dict[str, Any]:
    ledgers = root / "ledgers"
    candidates = read_jsonl(ledgers / "candidate_bank.jsonl")
    selectors = read_jsonl(ledgers / "selector_eval.jsonl")
    e2e = read_jsonl(ledgers / "e2e_runs.jsonl")
    adjudications = read_jsonl(ledgers / "adjudications.jsonl")

    candidate_cost = sum(_row_cost(row, "generator_model") for row in candidates)
    provider_selectors = [row for row in selectors if row.get("selector_name") in PROVIDER_SELECTOR_NAMES]
    selector_cost = sum(
        estimate_openai_cost(
            str(row.get("model") or row.get("selector_model") or MODEL_DEFAULT),
            int(row.get("selector_input_tokens") or 0),
            int(row.get("selector_output_tokens") or 0),
            cached_input_tokens=int(row.get("selector_cached_input_tokens") or 0),
        )
        for row in provider_selectors
    )
    adjudication_cost = sum(
        estimate_openai_cost(
            str(row.get("model") or MODEL_DEFAULT),
            int(row.get("input_tokens") or 0),
            int(row.get("output_tokens") or 0),
            cached_input_tokens=int(row.get("cached_input_tokens") or 0),
        )
        for row in adjudications
    )
    selector_average = selector_cost / len(provider_selectors) if provider_selectors else 0.0
    e2e_provider_rows = [row for row in e2e if row.get("pipeline_name") in PROVIDER_E2E_PIPELINES]
    e2e_selection_estimated = selector_average * len(e2e_provider_rows)
    total = candidate_cost + selector_cost + adjudication_cost + e2e_selection_estimated
    return {
        "root": str(root),
        "model": MODEL_DEFAULT,
        "candidate_rows": len(candidates),
        "selector_rows": len(selectors),
        "provider_selector_rows": len(provider_selectors),
        "e2e_provider_selection_rows_estimated": len(e2e_provider_rows),
        "adjudication_rows": len(adjudications),
        "candidate_generation_cost_usd": round(candidate_cost, 6),
        "provider_selector_cost_usd": round(selector_cost, 6),
        "adjudication_cost_usd": round(adjudication_cost, 6),
        "e2e_provider_selection_estimated_usd": round(e2e_selection_estimated, 6),
        "corrected_total_usd": round(total, 6),
        "pricing": budget_policy()["model_policy"],
    }


def bootstrap(root: Path = RESEARCH_DEFAULT_ROOT) -> dict[str, Any]:
    p = paths(root)
    ensure_tree(p)
    ensure_hidden_oracles(Path("artifacts/vericoding_research_v2_hidden_oracles"))
    previous = _read_state(p)
    policy = budget_policy()
    task_pool = _research_task_pool()
    write_json(p.manifests_dir / "task_pool.json", task_pool)
    write_json(p.manifests_dir / "dev_manifest.json", _research_manifest(split_manifest(task_pool, "dev")))
    write_json(
        p.manifests_dir / "confirmatory_manifest.json",
        _research_manifest(split_manifest(task_pool, "confirmatory")),
    )
    _write_primary_anchor_manifests(p, task_pool)
    for surface in ("internal", "scbench_regression", "terminalbench_guardrail", "secure"):
        write_json(
            p.manifests_dir / f"{surface}_manifest.json",
            _research_manifest(surface_manifest(task_pool, surface)),
        )
    _write_eval_sets(p)
    _initialize_queue(p, task_pool)
    write_json(p.config_dir / "budget_policy.json", policy)
    write_json(
        p.config_dir / "params.json",
        {
            "program_version": RESEARCH_PROGRAM_VERSION,
            "default_model": MODEL_DEFAULT,
            "canonical_root": str(root),
            "primary_anchor": {
                "primary_surfaces": sorted(PRIMARY_SURFACES),
                "primary_core_task_target": PRIMARY_CORE_TASK_TARGET,
                "main_claim": (
                    "Oracle-diverse generation creates candidate support, and regression-sensitive plus "
                    "security-sensitive hidden evaluators convert that support into better selection."
                ),
                "secondary_surfaces": sorted(SECONDARY_SURFACES),
                "tertiary_surfaces": sorted(TERTIARY_SURFACES),
            },
            "prior_roots": {
                "vericoding_depth_v2": "live calibration milestone",
                "vericoding_research_v1": "first claim-bearing partial program",
            },
            "target_identity": "oracle-diverse regression-sensitive secure vericoding conference program",
            "generation_modes": list(ORACLE_GENERATION_MODES),
            "pool_regimes": list(POOL_REGIMES),
            "full_live_launch_blocked_until": [
                "discriminability_pilot_passed",
                "resume_rehearsal_passed",
                "clean_launch_checkpoint_recorded",
            ],
            "manifest_freeze": "pre_pilot_sanitized_task_identity_frozen",
        },
    )
    _write_control_docs(p)
    _write_primary_claim_lock(p)
    v2 = recompute_v2_corrected_cost()
    _write_report(
        p,
        "v2_calibration_note.md",
        "Vericoding Depth v2 Calibration Note",
        [
            "The conference program treats `runs/vericoding_depth_v2/` as live calibration evidence, not final claim-bearing evidence.",
            f"Corrected v2 spend estimate under `{MODEL_DEFAULT}` pricing: `${v2['corrected_total_usd']:.4f}`.",
            f"Candidate generation corrected cost: `${v2['candidate_generation_cost_usd']:.4f}`.",
            f"Provider selector corrected cost: `${v2['provider_selector_cost_usd']:.4f}`.",
            f"Repair corrected cost: `${v2['adjudication_cost_usd']:.4f}`.",
            f"E2E provider-selection estimated cost: `${v2['e2e_provider_selection_estimated_usd']:.4f}`.",
        ],
    )
    _write_report(
        p,
        "v1_prior_milestone_note.md",
        "Vericoding Research v1 Prior Milestone",
        [
            "`runs/vericoding_research_v1/` is preserved as a real but partial claim-bearing prior program.",
            "Its strongest role is calibration for live orchestration, secure hidden-oracle execution, and visible-vs-hidden diagnostic signal.",
            "The conference program does not upgrade v1 claims; v2 ledgers are the canonical truth for new conference claims.",
        ],
    )
    _write_report(
        p,
        "phase_00_bootstrap.md",
        "Vericoding Research v2 Bootstrap",
        [
            "Budget policy is evidence-yield oriented and model-pinned to short-context `gpt-5.4-mini` for breadth.",
            "Full live launch remains blocked until discriminability pilot and resume rehearsal pass.",
            "Prompt bloat is treated as a stop condition requiring explicit model/budget reauthorization.",
            "The program is organized around oracle-diverse candidate support, visible-vs-hidden disagreement, secure rejection, bounded repair, and a narrow executable-property slice.",
            "The revised primary anchor is the owned 32-task core suite: internal regression-sensitive tasks plus secure rejection tasks.",
            "SCBench and Terminal-Bench are transfer/validity surfaces only and must not become the main denominator.",
        ],
    )
    state = {
        "program_version": RESEARCH_PROGRAM_VERSION,
        "current_phase": "bootstrapped",
        "phase_status": "blocked_before_live_scaling",
        "budget_policy_hash": stable_hash(policy),
        "task_pool_hash": task_pool["manifest_sha256"],
        "budget_used": 0.0,
        "provider_calls_completed": 0,
        "live_rows_completed": 0,
        "harbor_jobs_completed": 0,
        "discriminability_pilot_passed": False,
        "resume_rehearsal_passed": False,
        "clean_launch_checkpoint_recorded": False,
        "last_heartbeat_at": now_iso(),
        "last_successful_command": "bootstrap",
        "next_required_action": "run harness validation and discriminability pilot under the $2 pilot cap",
        "blockers": ["pilot_pending", "resume_rehearsal_pending", "clean_checkpoint_pending"],
        "v2_corrected_cost": v2,
    }
    for key in (
        "preflight",
        "clean_launch_checkpoint_recorded",
        "clean_launch",
        "launch_git_commit",
        "launch_diff_fingerprint",
        "launch_dirty_override",
        "run_root",
        "discriminability_pilot_passed",
        "resume_rehearsal_passed",
    ):
        if key in previous:
            state[key] = previous[key]
    write_json(p.state_dir / "program_state.json", state)
    return state


def preflight(
    *,
    root: Path = RESEARCH_DEFAULT_ROOT,
    model: str = MODEL_DEFAULT,
    allow_dirty_live: bool = False,
) -> dict[str, Any]:
    p = paths(root)
    ensure_tree(p)
    report = preflight_report(model=model, allow_dirty_live=allow_dirty_live)
    _write_report(
        p,
        "phase_00_preflight.md",
        "Vericoding Research v2 Preflight",
        [
            f"Model: `{model}`",
            f"OpenAI key visible: `{report['openai_api_key_present']}`",
            f"Provider minimal request: `{report['provider_minimal_request']['ok']}`",
            f"Harbor available: `{report['harbor_available']}`",
            f"Inspect import available: `{report['inspect_import_available']}`",
            f"Research v2 hidden-oracle dir ignored: `{_git_ignored('artifacts/vericoding_research_v2_hidden_oracles')}`",
            "Child subprocesses must use the sourced-shell environment or a recorded verified inherited environment.",
        ],
    )
    state = _read_state(p)
    state.update(
        {
            "program_version": RESEARCH_PROGRAM_VERSION,
            "current_phase": "preflight",
            "phase_status": "preflight_complete",
            "preflight": report,
            "last_heartbeat_at": now_iso(),
            "last_successful_command": "preflight",
        }
    )
    if not report["runner_git_dirty"] and not allow_dirty_live:
        state.update(
            {
                "clean_launch_checkpoint_recorded": True,
                "clean_launch": True,
                "launch_git_commit": report["runner_git_commit"],
                "launch_diff_fingerprint": report["diff_fingerprint"],
                "launch_dirty_override": False,
                "run_root": str(root),
            }
        )
    write_json(p.state_dir / "program_state.json", state)
    return report


def validate_launch_gates(root: Path = RESEARCH_DEFAULT_ROOT) -> dict[str, Any]:
    state = _read_state(paths(root))
    required = {
        "discriminability_pilot_passed": bool(state.get("discriminability_pilot_passed")),
        "resume_rehearsal_passed": bool(state.get("resume_rehearsal_passed")),
        "clean_launch_checkpoint_recorded": bool(state.get("clean_launch_checkpoint_recorded")),
    }
    return {
        "ok": all(required.values()),
        "required": required,
        "missing": [key for key, ok in required.items() if not ok],
    }


def run_all_live(
    *,
    root: Path = RESEARCH_DEFAULT_ROOT,
    model: str = MODEL_DEFAULT,
    allow_dirty_live: bool = False,
    allow_full_live: bool = False,
    rehearsal_stop_after: int | None = None,
    resume_mode: bool = False,
) -> int:
    p = paths(root)
    ensure_tree(p)
    state_before = _read_state(p)
    provenance_obj = assert_clean_or_sanctioned_run_root(
        run_root=root,
        allow_dirty_live=allow_dirty_live,
        state=state_before,
        resume=resume_mode,
    )
    gates = validate_launch_gates(root)
    if not gates["ok"] and not allow_full_live:
        _write_report(
            p,
            "phase_01_launch_gate.md",
            "Launch Gate",
            [
                "Full conference-program live scaling is intentionally blocked before the pilot and rehearsal gates pass.",
                f"Missing gates: `{', '.join(gates['missing'])}`.",
                "This is a launch-safety stop, not a completed empirical run.",
            ],
        )
        state = _read_state(p)
        state.update(
            {
                "program_version": RESEARCH_PROGRAM_VERSION,
                "current_phase": "launch_gate",
                "phase_status": "blocked",
                "last_heartbeat_at": now_iso(),
                "last_successful_command": "run-all-live",
                "next_required_action": "complete discriminability pilot and resume rehearsal before full launch",
                "blockers": gates["missing"],
            }
        )
        write_json(p.state_dir / "program_state.json", state)
        return 3
    started = time.monotonic()
    try:
        if resume_mode:
            _record_resume_acceptance(p, provenance_obj)
            task_pool = _load_task_pool(p)
        else:
            if not (p.manifests_dir / "task_pool.json").exists():
                bootstrap(root)
            task_pool = _load_task_pool(p)
            _record_clean_launch(p, provenance_obj, root=root)
        primary = {"tasks": _primary_tasks(task_pool)}
        candidate_rows = live_candidate_bank(
            p,
            primary,
            model=model,
            provenance=provenance_obj.to_dict(),
            rehearsal_stop_after=rehearsal_stop_after,
            phase="primary_core_candidate_bank",
        )
        primary_candidate_rows = [row for row in candidate_rows if row.get("surface") in PRIMARY_SURFACES]
        if rehearsal_stop_after is not None:
            _set_state(p, "rehearsal_interrupted", blockers=["deliberate_rehearsal_interrupt"])
            return 75
        selector_phase(p, primary_candidate_rows, split="dev", model=model)
        freeze_core(root=root)
        selector_phase(p, primary_candidate_rows, split="confirmatory", model=model)
        e2e_phase(p, primary_candidate_rows, model=model, provenance=provenance_obj.to_dict())
        secure_phase(p, primary_candidate_rows)
        analyze(root=root, started_monotonic=started)
        transfer_phase(root=root, model=model, provenance=provenance_obj.to_dict())
        external_phase(root=root)
        formal_overlay_phase(root=root)
        inspect_exports_phase(p)
        analyze(root=root, started_monotonic=started)
        export_paper(root=root)
        complete = _run_success_contract(p)
        _set_state(p, "complete" if complete else "downgraded_complete")
        return 0 if complete else 2
    except Exception as exc:
        _set_state(p, "stopped", blockers=[str(exc)])
        raise


def resume(
    *,
    root: Path = RESEARCH_DEFAULT_ROOT,
    model: str = MODEL_DEFAULT,
    allow_dirty_live: bool = False,
    rehearsal_stop_after: int | None = None,
) -> int:
    return run_all_live(
        root=root,
        model=model,
        allow_dirty_live=allow_dirty_live,
        allow_full_live=True,
        rehearsal_stop_after=rehearsal_stop_after,
        resume_mode=True,
    )


def pilot_live(
    *,
    root: Path = RESEARCH_DEFAULT_ROOT,
    model: str = MODEL_DEFAULT,
    allow_dirty_live: bool = False,
) -> int:
    p = paths(root)
    ensure_tree(p)
    if not (p.manifests_dir / "task_pool.json").exists():
        bootstrap(root)
    state = _read_state(p)
    provenance_obj = assert_clean_or_sanctioned_run_root(
        run_root=root,
        allow_dirty_live=allow_dirty_live,
        state=state,
        resume=False,
    )
    task_pool = _load_task_pool(p)
    dev_tasks = [
        task
        for task in task_pool["tasks"]
        if task["split"] == "dev" and task["surface"] in PRIMARY_SURFACES
    ]
    live_candidate_bank(
        p,
        {"tasks": dev_tasks},
        model=model,
        provenance=provenance_obj.to_dict(),
        quota_override={surface: 6 for surface in RESEARCH_PER_TASK_QUOTAS},
        phase="pilot_live",
    )
    report = _pilot_gate_report(p)
    state = _reconciled_state(p, "pilot_live")
    state["discriminability_pilot_passed"] = bool(report["pilot_passed"])
    state["blockers"] = [] if report["pilot_passed"] else report["failed_surfaces"]
    state["next_required_action"] = "run resume rehearsal" if report["pilot_passed"] else "redesign or downgrade failed pilot surfaces"
    write_json(p.state_dir / "program_state.json", state)
    return 0 if report["pilot_passed"] else 4


def run_core_dev(
    *,
    root: Path = RESEARCH_DEFAULT_ROOT,
    model: str = MODEL_DEFAULT,
    allow_dirty_live: bool = False,
    rehearsal_stop_after: int | None = None,
) -> int:
    p = paths(root)
    ensure_tree(p)
    if not (p.manifests_dir / "task_pool.json").exists():
        bootstrap(root)
    state = _read_state(p)
    provenance_obj = assert_clean_or_sanctioned_run_root(
        run_root=root,
        allow_dirty_live=allow_dirty_live,
        state=state,
        resume=False,
    )
    task_pool = _load_task_pool(p)
    dev_tasks = [
        task for task in _primary_tasks(task_pool) if task["split"] == "dev"
    ]
    rows = live_candidate_bank(
        p,
        {"tasks": dev_tasks},
        model=model,
        provenance=provenance_obj.to_dict(),
        phase="core_dev",
        rehearsal_stop_after=rehearsal_stop_after,
    )
    if rehearsal_stop_after is not None:
        _set_state(p, "core_dev_rehearsal_interrupted", blockers=["deliberate_rehearsal_interrupt"])
        return 75
    selector_phase(p, rows, split="dev", model=model)
    _write_primary_support_ledgers(p)
    analyze(root=root)
    return 0


def freeze_core(*, root: Path = RESEARCH_DEFAULT_ROOT) -> dict[str, Any]:
    p = paths(root)
    freeze_selector_semantics(p)
    freeze = {
        "program_version": RESEARCH_PROGRAM_VERSION,
        "frozen_at": now_iso(),
        "primary_anchor": "owned 32-task core suite",
        "primary_surfaces": sorted(PRIMARY_SURFACES),
        "support_accounting_schema": "hidden_correct / secure_passing / regression_clean by task, pool, and oracle",
        "secure_claim_predicate": "secure false-accept reduction, not hidden-pass existence",
        "repair_protocol": "one bounded provider-backed repair, reevaluated through harness",
        "secondary_surfaces": sorted(SECONDARY_SURFACES),
        "tertiary_surfaces": sorted(TERTIARY_SURFACES),
    }
    write_json(p.state_dir / "core_freeze.json", freeze)
    _write_report(
        p,
        "core_freeze_report.md",
        "Primary Core Freeze",
        [
            "Primary core manifests, selector semantics, support accounting, secure false-accept predicate, and repair protocol are frozen.",
            "SCBench remains secondary transfer; Terminal-Bench and formal overlay remain tertiary/supporting.",
        ],
    )
    state = _reconciled_state(p, "core_frozen")
    state["core_frozen"] = True
    write_json(p.state_dir / "program_state.json", state)
    return freeze


def run_core_confirmatory(
    *,
    root: Path = RESEARCH_DEFAULT_ROOT,
    model: str = MODEL_DEFAULT,
    allow_dirty_live: bool = False,
) -> int:
    p = paths(root)
    ensure_tree(p)
    state = _read_state(p)
    provenance_obj = assert_clean_or_sanctioned_run_root(
        run_root=root,
        allow_dirty_live=allow_dirty_live,
        state=state,
        resume=False,
    )
    task_pool = _load_task_pool(p)
    confirmatory = [
        task for task in _primary_tasks(task_pool) if task["split"] == "confirmatory"
    ]
    rows = live_candidate_bank(
        p,
        {"tasks": confirmatory},
        model=model,
        provenance=provenance_obj.to_dict(),
        phase="core_confirmatory",
    )
    selector_phase(p, rows, split="confirmatory", model=model)
    e2e_phase(p, rows, model=model, provenance=provenance_obj.to_dict())
    secure_phase(p, rows)
    _write_primary_support_ledgers(p)
    analyze(root=root)
    return 0


def transfer_phase(
    *,
    root: Path = RESEARCH_DEFAULT_ROOT,
    model: str = MODEL_DEFAULT,
    provenance: dict[str, Any] | None = None,
    allow_dirty_live: bool = False,
) -> int:
    p = paths(root)
    ensure_tree(p)
    state = _read_state(p)
    if provenance is None:
        provenance_obj = assert_clean_or_sanctioned_run_root(
            run_root=root,
            allow_dirty_live=allow_dirty_live,
            state=state,
            resume=False,
        )
        provenance = provenance_obj.to_dict()
    task_pool = _load_task_pool(p)
    scbench = _tasks_for_surfaces(task_pool, SECONDARY_SURFACES)
    rows = live_candidate_bank(
        p,
        {"tasks": scbench},
        model=model,
        provenance=provenance,
        phase="scbench_transfer",
    )
    write_csv(p.metrics_dir / "scbench_transfer_metrics.csv", _candidate_summary([r for r in rows if r.get("surface") == "scbench_regression"]))
    _write_report(
        p,
        "scbench_transfer_status.md",
        "SCBench Transfer Status",
        [
            "SCBench is secondary transfer evidence only.",
            "Rows are downgraded unless `surface_evidence_quality` is upgraded to sanitized executable SCBench evidence.",
        ],
    )
    analyze(root=root)
    return 0


def external_phase(*, root: Path = RESEARCH_DEFAULT_ROOT) -> int:
    p = paths(root)
    ensure_tree(p)
    rows = read_jsonl(p.ledgers_dir / "candidate_bank.jsonl")
    external_guardrail_phase(p, rows)
    _write_report(
        p,
        "external_validity_note.md",
        "External Validity Note",
        [
            "Terminal-Bench remains tertiary face-validity evidence.",
            "Fresh Harbor rows are supporting only and never become the primary denominator.",
        ],
    )
    analyze(root=root)
    return 0


def formal_overlay_phase(*, root: Path = RESEARCH_DEFAULT_ROOT) -> int:
    p = paths(root)
    ensure_tree(p)
    rows = read_jsonl(p.ledgers_dir / "candidate_bank.jsonl")
    formal_slice_phase(p, [row for row in rows if row.get("surface") in PRIMARY_SURFACES])
    analyze(root=root)
    return 0


def resume_rehearsal(
    *,
    root: Path = RESEARCH_DEFAULT_ROOT,
    model: str = MODEL_DEFAULT,
    allow_dirty_live: bool = False,
) -> int:
    p = paths(root)
    ensure_tree(p)
    if not (p.manifests_dir / "task_pool.json").exists():
        bootstrap(root)
    before = len(read_jsonl(p.ledgers_dir / "candidate_bank.jsonl"))
    first = run_all_live(
        root=root,
        model=model,
        allow_dirty_live=allow_dirty_live,
        allow_full_live=True,
        rehearsal_stop_after=3,
    )
    mid = len(read_jsonl(p.ledgers_dir / "candidate_bank.jsonl"))
    second = resume(
        root=root,
        model=model,
        allow_dirty_live=allow_dirty_live,
        rehearsal_stop_after=6,
    )
    after = len(read_jsonl(p.ledgers_dir / "candidate_bank.jsonl"))
    rows = read_jsonl(p.ledgers_dir / "candidate_bank.jsonl")
    ids = [row["bank_row_id"] for row in rows]
    passed = first == 75 and second == 75 and after > mid > before and len(ids) == len(set(ids))
    _write_report(
        p,
        "resume_rehearsal_report.md",
        "Resume Rehearsal",
        [
            f"Rows before: `{before}`",
            f"Rows after first interruption: `{mid}`",
            f"Rows after resume continuation: `{after}`",
            f"No duplicate primary rows: `{len(ids) == len(set(ids))}`",
            f"Passed: `{passed}`",
        ],
    )
    state = _reconciled_state(p, "resume_rehearsal")
    state["resume_rehearsal_passed"] = passed
    state["blockers"] = [] if passed else ["resume_rehearsal_failed"]
    state["next_required_action"] = "record clean launch checkpoint" if passed else "fix resume rehearsal"
    write_json(p.state_dir / "program_state.json", state)
    return 0 if passed else 5


def status(root: Path = RESEARCH_DEFAULT_ROOT) -> dict[str, Any]:
    p = paths(root)
    state = _reconciled_state(p, (_read_state(p).get("current_phase") or "status"))
    ledgers = p.ledgers_dir
    return {
        "program_version": RESEARCH_PROGRAM_VERSION,
        "root": str(root),
        "state": state,
        "queue": _queue_counts(p),
        "candidate_rows": len(read_jsonl(ledgers / "candidate_bank.jsonl")),
        "primary_candidate_rows": sum(
            1 for row in read_jsonl(ledgers / "candidate_bank.jsonl") if row.get("surface") in PRIMARY_SURFACES
        ),
        "selector_rows": len(read_jsonl(ledgers / "selector_eval.jsonl")),
        "e2e_rows": len(read_jsonl(ledgers / "e2e_runs.jsonl")),
        "secure_rows": len(read_jsonl(ledgers / "secure_eval.jsonl")),
        "external_rows": len(read_jsonl(ledgers / "external_guardrail.jsonl")),
        "formal_slice_rows": len(_read_formal_rows(p)),
        "support_analysis_rows": len(read_jsonl(ledgers / "support_analysis.jsonl")),
        "decomposition_rows": len(read_jsonl(ledgers / "decomposition_events.jsonl")),
        "launch_gates": validate_launch_gates(root),
    }


def _generation_plan(task: dict[str, Any], sample_index: int) -> dict[str, str]:
    mode = ORACLE_GENERATION_MODES[sample_index % len(ORACLE_GENERATION_MODES)]
    surface = task["surface"]
    condition = _condition_for_generation_mode(surface, mode)
    return {
        "generation_mode": mode,
        "condition": condition,
        "candidate_condition_id": mode,
        "oracle_family": _oracle_family(mode),
        "pool_regime": _pool_regime_for_generation_mode(mode),
    }


def _condition_for_generation_mode(surface: str, mode: str) -> str:
    if surface in {"internal", "secure"}:
        mapping = {
            "baseline": "baseline_prompt",
            "zen_oracle": "structural_discipline_prompt",
            "karpathy_oracle": "concise_prompt",
            "hybrid_structural_gate": "requirements_first_prompt",
            "baseline_plus_repair_seed": "spec_conditioned_prompt",
            "zen_plus_repair_seed": "structural_discipline_prompt",
            "karpathy_plus_repair_seed": "concise_prompt",
        }
    elif surface == "scbench_regression":
        mapping = {
            "baseline": "baseline_scbench_prompt",
            "zen_oracle": "regression_preservation_prompt",
            "karpathy_oracle": "concise_scbench_prompt",
            "hybrid_structural_gate": "spec_conditioned_scbench_prompt",
            "baseline_plus_repair_seed": "baseline_scbench_prompt",
            "zen_plus_repair_seed": "regression_preservation_prompt",
            "karpathy_plus_repair_seed": "concise_scbench_prompt",
        }
    else:
        mapping = {
            "baseline": "baseline_terminal_agent",
            "zen_oracle": "portable_structural_prompt_condition",
            "karpathy_oracle": "requirements_first_terminal_prompt",
            "hybrid_structural_gate": "portable_structural_prompt_condition",
            "baseline_plus_repair_seed": "baseline_terminal_agent",
            "zen_plus_repair_seed": "portable_structural_prompt_condition",
            "karpathy_plus_repair_seed": "requirements_first_terminal_prompt",
        }
    return mapping[mode]


def _oracle_family(mode: str) -> str:
    if mode.startswith("zen"):
        return "zen"
    if mode.startswith("karpathy"):
        return "karpathy"
    if mode.startswith("hybrid"):
        return "hybrid"
    if mode.endswith("repair_seed"):
        return "repair_seed"
    return "baseline"


def _pool_regime_for_generation_mode(mode: str) -> str:
    return GENERATION_MODE_POOL_REGIME.get(mode, "unknown")


def _effective_pool_regime(row: dict[str, Any]) -> str:
    mode = str(row.get("generation_mode") or "")
    return GENERATION_MODE_POOL_REGIME.get(mode) or str(row.get("pool_regime", "unknown"))


def live_candidate_bank(
    p: VericodingPaths,
    task_pool: dict[str, Any],
    *,
    model: str,
    provenance: dict[str, Any],
    quota_override: dict[str, int] | None = None,
    rehearsal_stop_after: int | None = None,
    phase: str = "live_candidate_bank",
) -> list[dict[str, Any]]:
    _watchdog_reconcile(p, "live_candidate_bank")
    existing = read_jsonl(p.ledgers_dir / "candidate_bank.jsonl")
    existing_ids = {row["bank_row_id"] for row in existing}
    emitted = 0
    quotas = quota_override or RESEARCH_PER_TASK_QUOTAS
    for task in task_pool["tasks"]:
        quota = quotas[task["surface"]]
        for sample_index in range(quota):
            plan = _generation_plan(task, sample_index)
            row_id = stable_hash(
                {
                    "program_version": RESEARCH_PROGRAM_VERSION,
                    "task_id": task["task_id"],
                    "condition": plan["candidate_condition_id"],
                    "sample_index": sample_index,
                },
                length=18,
            )
            if row_id in existing_ids:
                continue
            queue_condition = _candidate_queue_condition(plan["candidate_condition_id"], sample_index)
            _mark_queue_running(p, task, "live_candidate_bank", queue_condition)
            row = generate_live_candidate(
                task,
                condition=plan["condition"],
                sample_index=sample_index,
                model=model,
                artifact_dir=p.wrangled_dir / "live_candidates",
                provenance=provenance,
                program_version=RESEARCH_PROGRAM_VERSION,
                evaluation_mode="real_harness",
                candidate_condition_id=plan["candidate_condition_id"],
                extra_lineage={
                    "generation_mode": plan["generation_mode"],
                    "oracle_family": plan["oracle_family"],
                    "pool_regime": plan["pool_regime"],
                    "oracle_diverse_primary_evidence": True,
                },
            )
            row["support_type_candidates"] = _support_type_candidates(row)
            _validate_live_candidate_row(row)
            _append_unique(p.ledgers_dir / "candidate_bank.jsonl", [row], "bank_row_id")
            _mark_queue_completed(p, task, "live_candidate_bank", queue_condition, rows=1, artifacts=1)
            emitted += 1
            _event(p, phase, "candidate_row_emitted", {"task_id": task["task_id"], "row_id": row_id})
            _heartbeat(p, phase)
            _enforce_phase_budget(p, "pilot" if phase == "pilot_live" else "candidate_generation")
            if rehearsal_stop_after is not None and emitted >= rehearsal_stop_after:
                return read_jsonl(p.ledgers_dir / "candidate_bank.jsonl")
    rows = read_jsonl(p.ledgers_dir / "candidate_bank.jsonl")
    write_csv(p.wrangled_dir / "candidate_summary.csv", _candidate_summary(rows))
    _write_primary_support_ledgers(p)
    _write_report(
        p,
        "phase_05_candidate_bank.md" if phase != "pilot_live" else "pilot_candidate_bank.md",
        "Live Candidate Bank",
        [
            f"Live rows: `{len([r for r in rows if r.get('candidate_source_type') == 'live_model'])}`",
            f"Surface quotas met: `{_surface_quotas_met(rows)}`",
            f"Oracle families seen: `{sorted({r.get('oracle_family', 'unknown') for r in rows})}`",
            "Candidate labels are derived from surface harness routers and rows carry generation-mode / oracle-family provenance.",
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
    phase = f"selector_{split}"
    _watchdog_reconcile(p, phase)
    rows = []
    for (surface, task_id), pool in _group_candidates(candidate_rows, split=split).items():
        views = observable_views(pool)
        task_summary = f"{surface} task {task_id}; use only observable candidate evidence."
        for selector_name in SELECTORS:
            row_id = stable_hash(
                {
                    "program_version": RESEARCH_PROGRAM_VERSION,
                    "split": split,
                    "task_id": task_id,
                    "selector": selector_name,
                },
                length=18,
            )
            if _ledger_has(p.ledgers_dir / "selector_eval.jsonl", "selector_eval_row_id", row_id):
                continue
            _mark_simple_queue(p, surface, split, task_id, phase, selector_name, "running")
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
            selected = next(row for row in pool if row["candidate_id"] == chosen.candidate_id)
            out = _selector_row(
                row_id=row_id,
                surface=surface,
                split=split,
                task_id=task_id,
                selector_name=selector_name,
                selected=selected,
                candidate_pool_size=len(pool),
                meta=meta,
            )
            _append_unique(p.ledgers_dir / "selector_eval.jsonl", [out], "selector_eval_row_id")
            rows.append(out)
            _mark_simple_queue(p, surface, split, task_id, phase, selector_name, "completed")
            _heartbeat(p, phase)
            _enforce_phase_budget(p, "selector_eval")
    all_rows = read_jsonl(p.ledgers_dir / "selector_eval.jsonl")
    write_csv(p.wrangled_dir / "selector_summary.csv", all_rows)
    write_csv(p.metrics_dir / "selector_metrics.csv", _selector_metrics(all_rows))
    _write_report(
        p,
        "phase_06_selector_dev.md" if split == "dev" else "phase_07_selector_confirmatory.md",
        "Selector Dev" if split == "dev" else "Selector Confirmatory",
        [f"Selector rows for `{split}` complete."],
    )
    return rows


def freeze_selector_semantics(p: VericodingPaths) -> None:
    payload = {
        "program_version": RESEARCH_PROGRAM_VERSION,
        "frozen_at": now_iso(),
        "selectors": SELECTORS,
        "pipelines": PIPELINES,
        "prompt_token_limits": PROMPT_TOKEN_LIMITS,
        "row_validity_rules": "observable-only selectors; hidden labels joined only after selection",
    }
    write_json(p.state_dir / "selector_freeze.json", payload)
    _write_report(
        p,
        "selector_freeze_report.md",
        "Selector Semantics Freeze",
        ["Selector prompts, shortlist logic, schemas, and row-validity rules are frozen before confirmatory analysis."],
    )


def e2e_phase(
    p: VericodingPaths,
    candidate_rows: list[dict[str, Any]],
    *,
    model: str,
    provenance: dict[str, Any],
) -> list[dict[str, Any]]:
    _watchdog_reconcile(p, "e2e_confirmatory")
    rows = []
    repair_attempts = len(read_jsonl(p.ledgers_dir / "adjudications.jsonl"))
    for (surface, task_id), pool in _group_candidates(candidate_rows, split="confirmatory").items():
        task = _task_by_id(p, task_id)
        n = 3 if surface == "terminalbench_guardrail" else 4
        pool_n = pool[:n]
        views = observable_views(pool_n)
        for pipeline in PIPELINES:
            row_id = stable_hash(
                {"program_version": RESEARCH_PROGRAM_VERSION, "task_id": task_id, "pipeline": pipeline},
                length=18,
            )
            if _ledger_has(p.ledgers_dir / "e2e_runs.jsonl", "e2e_row_id", row_id):
                continue
            selected, selection_meta = _select_for_pipeline(
                pipeline,
                views,
                pool_n,
                task_id=task_id,
                model=model,
            )
            repair_applied = False
            repair_cost = 0.0
            repair_tokens = {"input": 0, "output": 0}
            if pipeline == "best_of_n_specoracle_plus_one_repair" and repair_attempts < 20:
                repaired, repair_row = repair_candidate_live(
                    selected,
                    task=task,
                    model=model,
                    repair_dir=p.wrangled_dir / "repairs",
                    provenance=provenance,
                    program_version=RESEARCH_PROGRAM_VERSION,
                    evaluation_mode="real_harness",
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
                "program_version": RESEARCH_PROGRAM_VERSION,
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
                "cost_usd": float(selection_meta.get("selector_cost_usd") or 0.0),
                "repair_cost_usd": repair_cost,
                "selected_candidate_generation_cost_usd": float(selected.get("cost_usd") or 0.0),
                "input_tokens": int(selection_meta.get("selector_input_tokens") or 0),
                "cached_input_tokens": int(selection_meta.get("selector_cached_input_tokens") or 0),
                "output_tokens": int(selection_meta.get("selector_output_tokens") or 0),
                "repair_input_tokens": repair_tokens["input"],
                "repair_output_tokens": repair_tokens["output"],
                "wall_seconds": float(selected.get("wall_seconds") or 0.0),
                "selector_wall_seconds": float(selection_meta.get("selector_wall_seconds") or 0.0),
                "selector_prompt_version": selection_meta.get("selector_prompt_version", ""),
                "comparison_count": int(selection_meta.get("comparison_count") or 0),
                "created_at": now_iso(),
            }
            _append_unique(p.ledgers_dir / "e2e_runs.jsonl", [out], "e2e_row_id")
            rows.append(out)
            _heartbeat(p, "e2e_confirmatory")
            _enforce_phase_budget(p, "e2e_repair")
    all_rows = read_jsonl(p.ledgers_dir / "e2e_runs.jsonl")
    write_csv(p.wrangled_dir / "e2e_summary.csv", all_rows)
    write_csv(p.metrics_dir / "e2e_metrics.csv", _e2e_metrics(all_rows))
    _write_report(p, "phase_08_e2e_confirmatory.md", "E2E Confirmatory", [f"E2E rows: `{len(all_rows)}`"])
    return rows


def secure_phase(p: VericodingPaths, candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in candidate_rows:
        if row["surface"] != "secure" or row["split"] != "confirmatory":
            continue
        code = Path(row["candidate_artifact_path"]).read_text(encoding="utf-8")
        secure = run_hidden_oracle(
            row["task_id"],
            code,
            root=Path("artifacts/vericoding_research_v2_hidden_oracles"),
        )
        secure.update(
            {
                "program_version": RESEARCH_PROGRAM_VERSION,
                "candidate_id": row["candidate_id"],
                "candidate_sha256": row["candidate_sha256"],
            }
        )
        _append_unique(p.ledgers_dir / "secure_eval.jsonl", [secure], "secure_eval_row_id")
        rows.append(secure)
    all_rows = read_jsonl(p.ledgers_dir / "secure_eval.jsonl")
    write_csv(p.wrangled_dir / "secure_summary.csv", all_rows)
    write_csv(p.metrics_dir / "secure_metrics.csv", _secure_metrics(all_rows))
    _write_report(p, "phase_09_secure_subset.md", "Secure Subset", [f"Executable hidden-oracle rows: `{len(all_rows)}`"])
    return rows


def formal_slice_phase(p: VericodingPaths, candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    overlay_task_ids = _formal_overlay_task_ids(p)
    secure_rows = [
        row
        for row in candidate_rows
        if row["surface"] == "secure"
        and row["split"] == "confirmatory"
        and row.get("visible_tests_pass")
        and row["task_id"] in overlay_task_ids
    ]
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in secure_rows:
        by_task[row["task_id"]].append(row)
    for task_id, task_rows in sorted(by_task.items())[:8]:
        for row in task_rows[:2]:
            code = Path(row["candidate_artifact_path"]).read_text(encoding="utf-8")
            prop = run_hidden_oracle(
                row["task_id"],
                code,
                root=Path("artifacts/vericoding_research_v2_hidden_oracles"),
            )
            out = {
                "formal_slice_row_id": stable_hash(
                    {
                        "program_version": RESEARCH_PROGRAM_VERSION,
                        "task_id": task_id,
                        "candidate_id": row["candidate_id"],
                        "backend": "executable_property_oracle",
                    },
                    length=18,
                ),
                "program_version": RESEARCH_PROGRAM_VERSION,
                "surface": "secure",
                "split": row["split"],
                "task_id": task_id,
                "candidate_id": row["candidate_id"],
                "semi_formal_backend": "executable_property_oracle",
                "visible_tests_pass": bool(row.get("visible_tests_pass")),
                "property_pass": bool(prop.get("hidden_passed")),
                "visible_property_disagreement": bool(row.get("visible_tests_pass")) != bool(prop.get("hidden_passed")),
                "surface_evidence_quality": "executable_property_oracle",
                "hidden_oracle_sha256": prop["hidden_oracle_sha256"],
                "raw_content_committed": False,
                "created_at": now_iso(),
            }
            _append_unique(p.ledgers_dir / "formal_slice_eval.jsonl", [out], "formal_slice_row_id")
            rows.append(out)
    all_rows = _read_formal_rows(p)
    write_csv(p.metrics_dir / "formal_slice_metrics.csv", _formal_slice_metrics(all_rows))
    write_csv(p.metrics_dir / "formal_overlay_metrics.csv", _formal_slice_metrics(all_rows))
    write_csv(p.wrangled_dir / "formal_overlay_disagreement.csv", all_rows)
    _write_report(
        p,
        "formal_overlay_status.md",
        "Narrow Executable-Property Formal Overlay",
        [
            f"Executable-property rows: `{len(all_rows)}`",
            "The overlay is capped to primary-core tasks and is not a separate main denominator.",
            "This is a semi-formal discriminator slice backed by executable hidden properties, not a broad formal-verification claim.",
        ],
    )
    _enforce_phase_budget(p, "formal_slice")
    return rows


def _read_formal_rows(p: VericodingPaths) -> list[dict[str, Any]]:
    rows = read_jsonl(p.ledgers_dir / "formal_slice_eval.jsonl")
    if not rows:
        rows = read_jsonl(p.ledgers_dir / "formal_slice.jsonl")
    overlay_task_ids = _formal_overlay_task_ids(p)
    return [row for row in rows if not overlay_task_ids or row.get("task_id") in overlay_task_ids]


def _formal_overlay_task_ids(p: VericodingPaths) -> set[str]:
    manifest_path = p.manifests_dir / "formal_overlay_manifest.json"
    if not manifest_path.exists():
        return set()
    manifest = read_json(manifest_path)
    return {str(task.get("task_id")) for task in manifest.get("tasks", [])}


def external_guardrail_phase(
    p: VericodingPaths,
    candidate_rows: list[dict[str, Any]],
    *,
    pilot_only: bool = False,
) -> list[dict[str, Any]]:
    _watchdog_reconcile(p, "external_guardrail")
    run_dir = p.root / "raw_jobs" / ("terminalbench_pilot" if pilot_only else "terminalbench_fresh_v2")
    if not any(run_dir.glob("raw_jobs/*/result.json")):
        _run_fresh_terminalbench_guardrail(run_dir, pilot_only=pilot_only)
    emitted = []
    for result_path in sorted(run_dir.glob("raw_jobs/*/result.json")):
        payload = read_json(result_path)
        stats = payload.get("stats") or {}
        completed = int(stats.get("n_completed_trials") or 0)
        row = {
            "external_guardrail_row_id": stable_hash(
                {"program_version": RESEARCH_PROGRAM_VERSION, "result": str(result_path), "id": payload.get("id")},
                length=18,
            ),
            "program_version": RESEARCH_PROGRAM_VERSION,
            "source": "fresh_harbor_terminalbench_v2",
            "source_result_path": str(result_path),
            "harbor_job_id": payload.get("id", ""),
            "started_at": payload.get("started_at", ""),
            "finished_at": payload.get("finished_at", ""),
            "completed_trials": completed,
            "errored_trials": int(stats.get("n_errored_trials") or 0),
            "running_trials": int(stats.get("n_running_trials") or 0),
            "pending_trials": int(stats.get("n_pending_trials") or 0),
            "surface_evidence_quality": "harbor_backend_sanitized_summary",
            "fresh_v2_external_evidence": True,
            "raw_content_committed": False,
            "created_at": now_iso(),
        }
        _append_unique(p.ledgers_dir / "external_guardrail.jsonl", [row], "external_guardrail_row_id")
        emitted.append(row)
        if pilot_only:
            break
    if not emitted:
        row = _external_attempt_row(run_dir, pilot_only=pilot_only)
        _append_unique(p.ledgers_dir / "external_guardrail.jsonl", [row], "external_guardrail_row_id")
    rows = read_jsonl(p.ledgers_dir / "external_guardrail.jsonl")
    _write_report(
        p,
        "phase_11_external_guardrail.md" if not pilot_only else "pilot_external_guardrail.md",
        "External Guardrail",
        [
            f"Fresh v2 sanitized Harbor rows/attempts: `{len(rows)}`",
            "Rows are fresh v2 Terminal-Bench guardrail summaries or explicit fresh backend attempts; raw job artifacts remain quarantined.",
        ],
    )
    return rows


def _run_fresh_terminalbench_guardrail(run_dir: Path, *, pilot_only: bool) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    task_limit = 1 if pilot_only else 2
    budget_cap = min(RESEARCH_PHASE_BUDGETS["external_harbor"], 4.0 if pilot_only else 8.0)
    command = (
        "source ~/.zshrc >/dev/null 2>&1; "
        "python3 scripts/run_terminalbench_artifact_gated.py run "
        f"--run-dir {run_dir.as_posix()} "
        f"--task-limit {task_limit} "
        "--force-all --allow-paid "
        f"--budget-cap-usd {budget_cap}"
    )
    metadata = {
        "program_version": RESEARCH_PROGRAM_VERSION,
        "command": command,
        "sourced_shell_env": True,
        "pilot_only": pilot_only,
        "created_at": now_iso(),
    }
    write_json(run_dir / "fresh_terminalbench_command.json", metadata)
    try:
        completed = subprocess.run(
            ["zsh", "-lc", command],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            timeout=3600 if not pilot_only else 1800,
            check=False,
        )
    except Exception as exc:
        write_json(
            run_dir / "fresh_terminalbench_attempt.json",
            {
                **metadata,
                "returncode": -1,
                "error": str(exc),
                "stdout_tail": "",
                "stderr_tail": "",
            },
        )
        return
    write_json(
        run_dir / "fresh_terminalbench_attempt.json",
        {
            **metadata,
            "returncode": completed.returncode,
            "stdout_tail": (completed.stdout or "")[-2000:],
            "stderr_tail": (completed.stderr or "")[-2000:],
        },
    )


def _external_attempt_row(run_dir: Path, *, pilot_only: bool) -> dict[str, Any]:
    attempt = read_json(run_dir / "fresh_terminalbench_attempt.json") if (run_dir / "fresh_terminalbench_attempt.json").exists() else {}
    return {
        "external_guardrail_row_id": stable_hash(
            {"program_version": RESEARCH_PROGRAM_VERSION, "run_dir": str(run_dir), "attempt": attempt},
            length=18,
        ),
        "program_version": RESEARCH_PROGRAM_VERSION,
        "source": "fresh_harbor_terminalbench_v2_attempt",
        "source_result_path": str(run_dir / "fresh_terminalbench_attempt.json"),
        "harbor_job_id": "",
        "completed_trials": 0,
        "errored_trials": 0,
        "running_trials": 0,
        "pending_trials": 0,
        "fresh_v2_external_evidence": True,
        "surface_evidence_quality": "harbor_backend_attempt_no_completed_result",
        "pilot_only": pilot_only,
        "returncode": attempt.get("returncode", ""),
        "raw_content_committed": False,
        "created_at": now_iso(),
    }


def inspect_exports_phase(p: VericodingPaths) -> None:
    _write_report(
        p,
        "phase_12_inspect_exports.md",
        "Inspect Exports",
        ["Inspect eval-set manifests point at sanitized conference-program ledgers and summaries."],
    )


def analyze(root: Path = RESEARCH_DEFAULT_ROOT, *, started_monotonic: float | None = None) -> dict[str, Any]:
    p = paths(root)
    ensure_tree(p)
    _write_primary_support_ledgers(p)
    candidates = read_jsonl(p.ledgers_dir / "candidate_bank.jsonl")
    selectors = read_jsonl(p.ledgers_dir / "selector_eval.jsonl")
    e2e = read_jsonl(p.ledgers_dir / "e2e_runs.jsonl")
    secure = read_jsonl(p.ledgers_dir / "secure_eval.jsonl")
    external = read_jsonl(p.ledgers_dir / "external_guardrail.jsonl")
    formal = _read_formal_rows(p)
    adjudications = read_jsonl(p.ledgers_dir / "adjudications.jsonl")
    write_csv(p.wrangled_dir / "candidate_summary.csv", _candidate_summary(candidates))
    write_csv(p.wrangled_dir / "selector_summary.csv", selectors)
    write_csv(p.wrangled_dir / "e2e_summary.csv", e2e)
    write_csv(p.wrangled_dir / "secure_summary.csv", secure)
    write_csv(p.wrangled_dir / "external_guardrail_summary.csv", external)
    write_csv(p.wrangled_dir / "formal_slice_summary.csv", formal)
    write_csv(p.wrangled_dir / "surface_summary.csv", _surface_summary(candidates, selectors, e2e, external))
    write_csv(p.wrangled_dir / "failure_taxonomy.csv", _failure_taxonomy(candidates))
    selector_metrics = _selector_metrics(selectors)
    e2e_metrics = _e2e_metrics(e2e)
    secure_metrics = _secure_metrics(secure)
    external_metrics = _external_metrics(external)
    formal_metrics = _formal_slice_metrics(formal)
    write_csv(p.metrics_dir / "selector_metrics.csv", selector_metrics)
    write_csv(p.metrics_dir / "e2e_metrics.csv", e2e_metrics)
    write_csv(p.metrics_dir / "secure_metrics.csv", secure_metrics)
    write_csv(p.metrics_dir / "external_guardrail_metrics.csv", external_metrics)
    write_csv(p.metrics_dir / "formal_slice_metrics.csv", formal_metrics)
    write_csv(p.metrics_dir / "formal_overlay_metrics.csv", formal_metrics)
    write_csv(p.metrics_dir / "budget_summary.csv", _budget_summary(candidates, selectors, e2e, adjudications, external))
    _write_primary_metric_exports(p, candidates, selectors, e2e)
    _write_mechanism_tables(p, candidates, selectors, e2e, adjudications, formal)
    primary_candidates = [row for row in candidates if row.get("surface") in PRIMARY_SURFACES]
    primary_selectors = [row for row in selectors if row.get("surface") in PRIMARY_SURFACES]
    primary_e2e = [row for row in e2e if row.get("surface") in PRIMARY_SURFACES]
    evidence = _ledger_evidence(candidates, selectors, e2e, secure, adjudications, external, started_monotonic, formal)
    evidence.update(_conference_claim_movement(primary_candidates, primary_selectors, primary_e2e, secure, formal))
    floors = empirical_floor_status(evidence)
    claims = claim_status_from_evidence(evidence)
    write_json(p.reports_dir / "claim_status.json", {"evidence": evidence, "floors": floors, "claims": claims})
    _write_claims(p, claims)
    _write_final_synthesis(p, evidence, floors, claims)
    write_json(p.state_dir / "program_state.json", _reconciled_state(p, "analyzed"))
    return {"evidence": evidence, "floors": floors, "claims": claims}


def export_paper(root: Path = RESEARCH_DEFAULT_ROOT) -> None:
    p = paths(root)
    for rel in ("paper_artifacts/tables", "paper_artifacts/figures", "paper_artifacts/appendix_cases"):
        (p.root / rel).mkdir(parents=True, exist_ok=True)
    for source, dest in (
        (p.manifests_dir / "task_pool.json", p.paper_dir / "tables/task_inventory.json"),
        (p.metrics_dir / "selector_metrics.csv", p.paper_dir / "tables/selector_metrics.csv"),
        (p.metrics_dir / "primary_core_selector_metrics.csv", p.paper_dir / "tables/primary_core_selector_metrics.csv"),
        (
            p.metrics_dir / "primary_core_selector_metrics.csv",
            p.paper_dir / "tables/support_conditioned_selector_accuracy.csv",
        ),
        (p.metrics_dir / "e2e_metrics.csv", p.paper_dir / "tables/e2e_metrics.csv"),
        (p.metrics_dir / "e2e_metrics.csv", p.paper_dir / "tables/e2e_by_surface.csv"),
        (p.metrics_dir / "primary_core_e2e_metrics.csv", p.paper_dir / "tables/primary_core_e2e_metrics.csv"),
        (p.metrics_dir / "secure_metrics.csv", p.paper_dir / "tables/secure_metrics.csv"),
        (p.metrics_dir / "primary_core_support_curves.csv", p.paper_dir / "tables/primary_core_support_curves.csv"),
        (p.metrics_dir / "primary_core_disagreement_metrics.csv", p.paper_dir / "tables/primary_core_disagreement_metrics.csv"),
        (p.metrics_dir / "primary_core_decomposition.csv", p.paper_dir / "tables/primary_core_decomposition.csv"),
        (p.wrangled_dir / "internal_hidden_disagreement.csv", p.paper_dir / "tables/internal_hidden_disagreement.csv"),
        (p.wrangled_dir / "internal_hidden_disagreement.csv", p.paper_dir / "tables/visible_vs_hidden_disagreement.csv"),
        (p.wrangled_dir / "secure_false_accept_by_selector.csv", p.paper_dir / "tables/secure_false_accept_by_selector.csv"),
        (p.metrics_dir / "scbench_transfer_metrics.csv", p.paper_dir / "tables/scbench_transfer_summary.csv"),
        (p.metrics_dir / "external_guardrail_metrics.csv", p.paper_dir / "tables/external_guardrail_metrics.csv"),
        (p.metrics_dir / "external_guardrail_metrics.csv", p.paper_dir / "tables/terminalbench_external_summary.csv"),
        (p.metrics_dir / "formal_slice_metrics.csv", p.paper_dir / "tables/formal_slice_selector_metrics.csv"),
        (p.metrics_dir / "formal_overlay_metrics.csv", p.paper_dir / "tables/formal_overlay_metrics.csv"),
        (p.metrics_dir / "formal_overlay_metrics.csv", p.paper_dir / "tables/formal_overlay_summary.csv"),
        (p.wrangled_dir / "surface_summary.csv", p.paper_dir / "tables/surface_summary.csv"),
    ):
        if source.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    for source, dest in (
        (p.reports_dir / "internal_visible_vs_hidden_casebook.md", p.paper_dir / "appendix_cases/internal_visible_vs_hidden_casebook.md"),
        (p.reports_dir / "secure_adversarial_casebook.md", p.paper_dir / "appendix_cases/secure_adversarial_casebook.md"),
        (p.reports_dir / "scbench_transfer_status.md", p.paper_dir / "appendix_cases/scbench_transfer_status.md"),
        (p.reports_dir / "external_validity_note.md", p.paper_dir / "appendix_cases/external_validity_note.md"),
        (p.reports_dir / "formal_overlay_status.md", p.paper_dir / "appendix_cases/formal_overlay_status.md"),
        (p.reports_dir / "final_synthesis.md", p.paper_dir / "appendix_cases/final_synthesis.md"),
        (p.reports_dir / "claim_status.json", p.paper_dir / "appendix_cases/claim_status.json"),
        (p.reports_dir / "phase_00_preflight.md", p.paper_dir / "appendix_cases/provenance_note.md"),
        (p.reports_dir / "selector_freeze_report.md", p.paper_dir / "appendix_cases/selector_freeze_report.md"),
    ):
        if source.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    (p.paper_dir / "figures/system_architecture.md").write_text(
        "# System Architecture\n\nInspect-native control plane with oracle-diverse provider generation, observable-only selectors, secure/regression hidden oracles, bounded repair, executable-property slice, and fresh Harbor-backed external guardrail summaries.\n",
        encoding="utf-8",
    )


def ensure_tree(p: VericodingPaths) -> None:
    for rel in (
        "config",
        "manifests/inspect_eval_sets",
        "ledgers",
        "data/raw",
        "data/wrangled",
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
    for name in (
        "candidate_bank.jsonl",
        "selector_eval.jsonl",
        "e2e_runs.jsonl",
        "secure_eval.jsonl",
        "external_guardrail.jsonl",
        "formal_slice_eval.jsonl",
        "formal_slice.jsonl",
        "adjudications.jsonl",
        "phase_events.jsonl",
        "watchdog_events.jsonl",
        "support_analysis.jsonl",
        "decomposition_events.jsonl",
    ):
        (p.ledgers_dir / name).touch(exist_ok=True)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Vericoding Research v2 conference-program orchestrator")
    parser.add_argument(
        "command",
        choices=[
            "preflight",
            "bootstrap",
            "pilot-live",
            "resume-rehearsal",
            "run-core-dev",
            "freeze-core",
            "run-core-confirmatory",
            "run-transfer",
            "run-external",
            "run-formal-slice",
            "run-all-live",
            "resume",
            "status",
            "analyze",
            "export-paper",
        ],
    )
    parser.add_argument("--root", type=Path, default=RESEARCH_DEFAULT_ROOT)
    parser.add_argument("--model", default=MODEL_DEFAULT)
    parser.add_argument("--allow-dirty-live", action="store_true")
    parser.add_argument("--allow-full-live", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.command == "preflight":
        preflight(root=args.root, model=args.model, allow_dirty_live=args.allow_dirty_live)
        return 0
    if args.command == "bootstrap":
        bootstrap(args.root)
        return 0
    if args.command == "pilot-live":
        return pilot_live(root=args.root, model=args.model, allow_dirty_live=args.allow_dirty_live)
    if args.command == "resume-rehearsal":
        return resume_rehearsal(root=args.root, model=args.model, allow_dirty_live=args.allow_dirty_live)
    if args.command == "run-core-dev":
        return run_core_dev(root=args.root, model=args.model, allow_dirty_live=args.allow_dirty_live)
    if args.command == "freeze-core":
        freeze_core(root=args.root)
        return 0
    if args.command == "run-core-confirmatory":
        return run_core_confirmatory(root=args.root, model=args.model, allow_dirty_live=args.allow_dirty_live)
    if args.command == "run-transfer":
        return transfer_phase(root=args.root, model=args.model, allow_dirty_live=args.allow_dirty_live)
    if args.command == "run-external":
        return external_phase(root=args.root)
    if args.command == "run-formal-slice":
        return formal_overlay_phase(root=args.root)
    if args.command == "status":
        print(json.dumps(status(args.root), indent=2, sort_keys=True))
        return 0
    if args.command == "analyze":
        analyze(root=args.root)
        return 0
    if args.command == "export-paper":
        export_paper(root=args.root)
        return 0
    if args.command == "run-all-live":
        return run_all_live(
            root=args.root,
            model=args.model,
            allow_dirty_live=args.allow_dirty_live,
            allow_full_live=args.allow_full_live,
        )
    if args.command == "resume":
        return resume(root=args.root, model=args.model, allow_dirty_live=args.allow_dirty_live)
    raise AssertionError(args.command)


def _floor_met(key: str, observed: Any, floor: Any) -> dict[str, Any]:
    try:
        observed_float = float(observed)
        floor_float = float(floor)
        met = observed_float >= floor_float
    except (TypeError, ValueError):
        observed_float = 0.0
        floor_float = float(floor)
        met = False
    return {"observed": observed_float, "floor": floor_float, "met": met}


def _row_cost(row: dict[str, Any], model_key: str) -> float:
    return estimate_openai_cost(
        str(row.get(model_key) or MODEL_DEFAULT),
        int(row.get("input_tokens") or 0),
        int(row.get("output_tokens") or 0),
        cached_input_tokens=int(row.get("cached_input_tokens") or 0),
    )


def _research_task_pool() -> dict[str, Any]:
    pool = _research_manifest(build_task_pool())
    pool.update(
        {
            "schema_version": "vericoding_research_v2_task_pool",
            "target_count": 48,
            "surface_evidence_quality_required": {
                "internal": "real_harness",
                "secure": "real_harness",
                "scbench_regression": "sanitized_scbench_executable_or_explicit_downgrade",
                "terminalbench_guardrail": "fresh_harbor_backend_sanitized_summary",
            },
            "manifest_freeze_status": "frozen_pre_pilot",
            "manifest_freeze_rule": (
                "Task identity and split are frozen before discriminability review; "
                "surfaces may be downgraded, not silently retuned."
            ),
        }
    )
    pool["manifest_sha256"] = stable_hash({k: v for k, v in pool.items() if k != "manifest_sha256"})
    return pool


def _research_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    updated = json.loads(json.dumps(manifest))
    updated["program_version"] = RESEARCH_PROGRAM_VERSION
    updated["raw_content_committed"] = False
    if "tasks" in updated:
        for task in updated["tasks"]:
            task["program_version"] = RESEARCH_PROGRAM_VERSION
            task["raw_content_committed"] = False
            task["hidden_oracle_root"] = "artifacts/vericoding_research_v2_hidden_oracles"
            if task["surface"] == "scbench_regression":
                task["evidence_quality_required"] = "sanitized_scbench_executable_or_explicit_downgrade"
            elif task["surface"] == "terminalbench_guardrail":
                task["evidence_quality_required"] = "harbor_backend_sanitized_summary"
            else:
                task["evidence_quality_required"] = "real_harness"
    updated["manifest_sha256"] = stable_hash(
        {key: value for key, value in updated.items() if key != "manifest_sha256"}
    )
    return updated


def _primary_tasks(task_pool: dict[str, Any]) -> list[dict[str, Any]]:
    return [task for task in task_pool["tasks"] if task["surface"] in PRIMARY_SURFACES]


def _tasks_for_surfaces(task_pool: dict[str, Any], surfaces: set[str]) -> list[dict[str, Any]]:
    return [task for task in task_pool["tasks"] if task["surface"] in surfaces]


def _manifest_from_tasks(
    tasks: list[dict[str, Any]],
    *,
    schema_version: str,
    name: str,
    role: str,
) -> dict[str, Any]:
    manifest = {
        "schema_version": schema_version,
        "program_version": RESEARCH_PROGRAM_VERSION,
        "name": name,
        "role": role,
        "raw_content_committed": False,
        "task_count": len(tasks),
        "tasks": tasks,
        "manifest_freeze_status": "frozen_pre_confirmatory",
        "manifest_freeze_rule": "Task identity and split are fixed before confirmatory execution; downgrade, do not silently reshape.",
    }
    manifest["manifest_sha256"] = stable_hash(
        {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    )
    return manifest


def _write_primary_anchor_manifests(p: VericodingPaths, task_pool: dict[str, Any]) -> None:
    primary = _primary_tasks(task_pool)
    internal = [task for task in primary if task["surface"] == "internal"]
    secure = [task for task in primary if task["surface"] == "secure"]
    primary_dev = [task for task in primary if task["split"] == "dev"]
    primary_confirmatory = [task for task in primary if task["split"] == "confirmatory"]
    scbench = _tasks_for_surfaces(task_pool, SECONDARY_SURFACES)
    terminal = _tasks_for_surfaces(task_pool, TERTIARY_SURFACES)
    overlay_candidates = [
        task
        for task in secure
        if task.get("split") == "confirmatory"
    ][:8]
    manifests = {
        "primary_core_task_pool.json": _manifest_from_tasks(
            primary,
            schema_version="vericoding_research_v2_primary_core_pool",
            name="primary_core_task_pool",
            role="paper-owned primary denominator: internal regression plus secure rejection",
        ),
        "primary_core_dev_manifest.json": _manifest_from_tasks(
            primary_dev,
            schema_version="vericoding_research_v2_primary_core_split",
            name="primary_core_dev_manifest",
            role="primary-core dev mechanism slice",
        ),
        "primary_core_confirmatory_manifest.json": _manifest_from_tasks(
            primary_confirmatory,
            schema_version="vericoding_research_v2_primary_core_split",
            name="primary_core_confirmatory_manifest",
            role="primary-core confirmatory denominator",
        ),
        "internal_regression_manifest.json": _manifest_from_tasks(
            internal,
            schema_version="vericoding_research_v2_primary_surface",
            name="internal_regression_manifest",
            role="owned regression-sensitive surface",
        ),
        "secure_rejection_manifest.json": _manifest_from_tasks(
            secure,
            schema_version="vericoding_research_v2_primary_surface",
            name="secure_rejection_manifest",
            role="owned secure-rejection surface",
        ),
        "scbench_transfer_manifest.json": _manifest_from_tasks(
            scbench,
            schema_version="vericoding_research_v2_secondary_surface",
            name="scbench_transfer_manifest",
            role="secondary transfer surface; never primary denominator",
        ),
        "terminalbench_guardrail_manifest.json": _manifest_from_tasks(
            terminal,
            schema_version="vericoding_research_v2_tertiary_surface",
            name="terminalbench_guardrail_manifest",
            role="tertiary face-validity Harbor guardrail",
        ),
        "formal_overlay_manifest.json": _manifest_from_tasks(
            overlay_candidates,
            schema_version="vericoding_research_v2_formal_overlay",
            name="formal_overlay_manifest",
            role="narrow executable-property overlay over primary core, capped at 6-8 tasks",
        ),
    }
    for filename, manifest in manifests.items():
        write_json(p.manifests_dir / filename, manifest)


def _write_eval_sets(p: VericodingPaths) -> None:
    eval_sets = {
        "candidate_bank_dev.yaml": ("vericoding_candidate_bank", "dev"),
        "candidate_bank_confirmatory.yaml": ("vericoding_candidate_bank", "confirmatory"),
        "selector_confirmatory.yaml": ("vericoding_selector_eval", "confirmatory"),
        "e2e_confirmatory.yaml": ("vericoding_e2e", "confirmatory"),
        "secure_confirmatory.yaml": ("vericoding_secure_subset", "confirmatory"),
        "external_guardrail.yaml": ("vericoding_external_guardrail", "confirmatory"),
    }
    for filename, (task_name, split) in eval_sets.items():
        (p.manifests_dir / "inspect_eval_sets" / filename).write_text(
            "\n".join(
                [
                    f"program_version: {RESEARCH_PROGRAM_VERSION}",
                    f"task: {task_name}",
                    f"split: {split}",
                    "raw_content_committed: false",
                    f"root: {p.root.as_posix()}",
                    "",
                ]
            ),
            encoding="utf-8",
        )


def _write_control_docs(p: VericodingPaths) -> None:
    (p.root / "AGENTS.md").write_text(
        "\n".join(
            [
                "# Vericoding Research v2 Agents",
                "",
                "Mission: run an oracle-diverse, regression-sensitive, security-sensitive vericoding conference program.",
                "",
                "Non-goals: do not modify `paper/`, do not reinterpret v1/v2-depth milestones, and do not claim from proxy surfaces without downgrade labels.",
                "",
                "Priority order: oracle-diverse candidate support, regression-sensitive vericoding, secure rejection, bounded repair, narrow executable-property slice.",
                "",
                "Paper anchor: 70% of attention stays on the owned primary core suite: 20 internal regression-sensitive tasks and 12 secure rejection tasks.",
                "SCBench is a secondary transfer surface. Terminal-Bench and the formal overlay are tertiary/supporting.",
                "",
                "Stop rules: stop or downgrade on raw leakage, hidden-label selector access, manifest freeze violation, unexecutable secure oracles, external backend failure, or budget overrun.",
                "",
                "Selectors must remain observable-only. Hidden labels are joined only after selection for scoring.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (p.root / "SPEC.md").write_text(
        "\n".join(
            [
                "# Vericoding Research v2 Conference Program",
                "",
                "This root is the conference-program successor to `runs/vericoding_research_v1/`.",
                "`runs/vericoding_depth_v2/` remains a live calibration milestone and `runs/vericoding_research_v1/` remains the first partial claim-bearing program.",
                "Main evidence must be oracle-diverse, harness-grounded, live-generated, ledger-derived, and Inspect-native.",
                "The primary scientific object is the paper-owned 32-task core suite, not SCBench, Terminal-Bench, Harbor, Inspect, or the orchestration substrate.",
                "",
                "Core thesis: specs are most useful as ranking and rejection oracles when they are regression-sensitive and security-sensitive, and their gains are mediated by candidate-bank support created by oracle-diverse generation.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (p.root / "CLAIMS.md").write_text(
        "\n".join(
            [
                "# Claims",
                "",
                "Claim 1: Oracle-diverse candidate banks create selector headroom. Status: `pending`.",
                "Claim 2: Hidden regression and secure properties reveal failures visible tests miss. Status: `pending`.",
                "Claim 3: Ranking helps on some surfaces and fails on others for support-driven reasons. Status: `pending`.",
                "Claim 4: Secure/property false acceptance is reduced by observable spec-conditioned selection. Status: `pending`.",
                "Claim 5: One bounded repair is a secondary gain mechanism on near-miss candidates. Status: `pending`.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (p.root / "TASK_REGISTRY.md").write_text(
        "# Task Registry\n\nPrimary manifests are `primary_core_task_pool.json`, `primary_core_dev_manifest.json`, `primary_core_confirmatory_manifest.json`, `internal_regression_manifest.json`, and `secure_rejection_manifest.json`. SCBench is secondary transfer; Terminal-Bench is tertiary face-validity. Task manifests are frozen after harness validation and pilot discriminability pass. Surfaces can be explicitly downgraded but not silently retuned.\n",
        encoding="utf-8",
    )


def _write_primary_claim_lock(p: VericodingPaths) -> None:
    (p.root / "PRIMARY_CLAIM_LOCK.md").write_text(
        "\n".join(
            [
                "# Primary Claim Lock",
                "",
                "Primary scientific object: a paper-owned spec-first core suite where oracle-diverse candidate generation, hidden regression-sensitive evaluation, and secure rejection can be measured cleanly and mechanistically.",
                "",
                "Primary claim: Oracle-diverse generation creates candidate support, and regression-sensitive plus security-sensitive hidden evaluators convert that support into better selection. When support is absent, ranking and bounded repair do not rescue performance.",
                "",
                "## Reviewer Questions",
                "",
                "Q1 Support: Does oracle-diverse generation increase hidden-correct, secure-passing, or regression-clean candidate support on the owned primary suite?",
                "",
                "Q2 Hidden Evaluator Necessity: How often do visible tests disagree with hidden regression-sensitive or secure-sensitive evaluators?",
                "",
                "Q3 Conditional Usefulness: Conditional on support, do ranking and bounded repair improve outcomes, and do gains vanish when support is absent?",
                "",
                "## Hierarchy",
                "",
                "Primary: 20 internal regression-sensitive tasks plus 12 secure rejection tasks.",
                "",
                "Secondary: SCBench sanitized executable transfer slice, downgraded if it remains proxy-level.",
                "",
                "Tertiary: Terminal-Bench Harbor guardrail and 6-8 task formal overlay.",
                "",
                "Anti-drift rule: choose primary-suite sharpness over benchmark breadth whenever they conflict.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_report(p: VericodingPaths, name: str, title: str, bullets: list[str]) -> None:
    body = [f"# {title}", "", f"Generated: `{now_iso()}`", "", *[f"- {item}" for item in bullets], ""]
    (p.reports_dir / name).write_text("\n".join(body), encoding="utf-8")


def _read_state(p: VericodingPaths) -> dict[str, Any]:
    path = p.state_dir / "program_state.json"
    if not path.exists():
        return {}
    return read_json(path)


def _load_task_pool(p: VericodingPaths) -> dict[str, Any]:
    path = p.manifests_dir / "task_pool.json"
    if not path.exists():
        raise RuntimeError("task_pool.json missing; run bootstrap first")
    return read_json(path)


def _record_clean_launch(p: VericodingPaths, provenance: RuntimeProvenance, *, root: Path) -> None:
    state = _read_state(p)
    if state.get("clean_launch_checkpoint_recorded") and state.get("clean_launch"):
        state["run_root"] = state.get("run_root") or str(root)
        write_json(p.state_dir / "program_state.json", state)
        return
    clean_launch = not provenance.runner_git_dirty and not provenance.dirty_override
    state.update(
        {
            "clean_launch": clean_launch,
            "clean_launch_checkpoint_recorded": clean_launch,
            "launch_git_commit": state.get("launch_git_commit") or provenance.runner_git_commit,
            "launch_diff_fingerprint": state.get("launch_diff_fingerprint") or provenance.diff_fingerprint,
            "run_root": str(root),
            "launch_dirty_override": provenance.dirty_override,
            "launch_sanctioned_dirty_run_root": provenance.sanctioned_dirty_run_root,
            "launch_sanctioned_dirty_paths": list(provenance.sanctioned_dirty_paths),
        }
    )
    write_json(p.state_dir / "program_state.json", state)


def _record_resume_acceptance(p: VericodingPaths, provenance: RuntimeProvenance) -> None:
    state = _read_state(p)
    state["last_resume"] = {
        "created_at": now_iso(),
        "sanctioned_dirty_run_root": provenance.sanctioned_dirty_run_root,
        "sanctioned_dirty_paths": list(provenance.sanctioned_dirty_paths),
        "dirty_override": provenance.dirty_override,
        "run_root": provenance.run_root,
    }
    write_json(p.state_dir / "program_state.json", state)


def _initialize_queue(p: VericodingPaths, task_pool: dict[str, Any]) -> None:
    queue_path = p.state_dir / "task_queue.json"
    if queue_path.exists():
        return
    items = []
    for task in task_pool["tasks"]:
        for sample_index in range(RESEARCH_PER_TASK_QUOTAS[task["surface"]]):
            plan = _generation_plan(task, sample_index)
            items.append(
                _queue_item(
                    task,
                    "live_candidate_bank",
                    _candidate_queue_condition(plan["candidate_condition_id"], sample_index),
                )
            )
    write_json(queue_path, {"program_version": RESEARCH_PROGRAM_VERSION, "items": items})


def _candidate_queue_condition(condition: str, sample_index: int) -> str:
    return f"{condition}:live{sample_index}"


def _queue_item(task: dict[str, Any], phase: str, condition: str) -> dict[str, Any]:
    now = now_iso()
    return dataclass_to_dict(
        TaskQueueItem(
            work_item_id=stable_hash(
                {"program_version": RESEARCH_PROGRAM_VERSION, "phase": phase, "task": task["task_id"], "condition": condition},
                length=18,
            ),
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
    _update_queue_item(p, task, phase, condition, status="running", started_at=now_iso())


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
        task,
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
    status_value: str,
) -> None:
    task = {"surface": surface, "split": split, "task_id": task_id}
    _update_queue_item(p, task, phase, condition, status=status_value)


def _update_queue_item(p: VericodingPaths, task: dict[str, Any], phase: str, condition: str, **updates: Any) -> None:
    queue_path = p.state_dir / "task_queue.json"
    queue = read_json(queue_path) if queue_path.exists() else {"program_version": RESEARCH_PROGRAM_VERSION, "items": []}
    item_id = stable_hash(
        {"program_version": RESEARCH_PROGRAM_VERSION, "phase": phase, "task": task["task_id"], "condition": condition},
        length=18,
    )
    item = next((item for item in queue["items"] if item["work_item_id"] == item_id), None)
    if item is None:
        item = _queue_item(task, phase, condition)
        queue["items"].append(item)
    item.update(updates)
    item["last_progress_at"] = now_iso()
    write_json(queue_path, queue)


def _candidate_sample_index(row: dict[str, Any]) -> int | None:
    suffix = str(row.get("candidate_id", "")).rsplit(":live", 1)
    if len(suffix) != 2:
        return None
    try:
        return int(suffix[1])
    except ValueError:
        return None


def _reconcile_candidate_queue_from_ledger(p: VericodingPaths) -> None:
    queue_path = p.state_dir / "task_queue.json"
    if not queue_path.exists():
        return
    queue = read_json(queue_path)
    items = queue.get("items", [])
    if not items:
        return
    rows = read_jsonl(p.ledgers_dir / "candidate_bank.jsonl")
    changed = False
    consumed_indexes: set[int] = set()
    now = now_iso()
    for row in rows:
        sample_index = _candidate_sample_index(row)
        candidates = []
        if sample_index is not None:
            if row.get("candidate_condition_id"):
                candidates.append(_candidate_queue_condition(str(row.get("candidate_condition_id")), sample_index))
            if row.get("generation_mode"):
                candidates.append(_candidate_queue_condition(str(row.get("generation_mode")), sample_index))
            candidates.append(_candidate_queue_condition(str(row.get("generator_condition", "")), sample_index))
        candidates.append(str(row.get("generator_condition", "")))
        if row.get("candidate_condition_id"):
            candidates.append(str(row.get("candidate_condition_id")))
        for index, item in enumerate(items):
            if index in consumed_indexes:
                continue
            if item.get("phase") != "live_candidate_bank":
                continue
            if item.get("surface") != row.get("surface") or item.get("split") != row.get("split"):
                continue
            if item.get("task_id") != row.get("task_id"):
                continue
            if item.get("condition_or_pipeline") not in candidates:
                continue
            consumed_indexes.add(index)
            if item.get("status") != "completed":
                item.update(
                    {
                        "status": "completed",
                        "started_at": item.get("started_at") or row.get("created_at") or now,
                        "completed_at": item.get("completed_at") or row.get("created_at") or now,
                        "last_progress_at": now,
                        "ledger_rows_emitted": max(int(item.get("ledger_rows_emitted") or 0), 1),
                        "artifact_count": max(int(item.get("artifact_count") or 0), 1),
                        "stop_reason": "",
                    }
                )
                changed = True
            break
    if changed:
        write_json(queue_path, queue)


def _watchdog_reconcile(p: VericodingPaths, phase: str, *, now: datetime | None = None) -> list[dict[str, Any]]:
    queue_path = p.state_dir / "task_queue.json"
    if not queue_path.exists():
        return []
    queue = read_json(queue_path)
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
        append_jsonl(
            p.ledgers_dir / "watchdog_events.jsonl",
            [
                {
                    "event_id": stable_hash({"phase": phase, "items": stalled, "created_at": now_iso()}, length=18),
                    "program_version": RESEARCH_PROGRAM_VERSION,
                    "phase": phase,
                    "stalled_count": len(stalled),
                    "created_at": now_iso(),
                }
            ],
        )
    return stalled


def _heartbeat(p: VericodingPaths, phase: str) -> None:
    state = _reconciled_state(p, phase)
    write_json(p.state_dir / "program_state.json", state)


def _set_state(p: VericodingPaths, phase: str, *, blockers: list[str] | None = None) -> None:
    state = _reconciled_state(p, phase)
    state["blockers"] = blockers or []
    state["phase_status"] = phase
    if phase in {"complete", "downgraded_complete"}:
        state["next_required_action"] = "none; terminal phase complete"
    write_json(p.state_dir / "program_state.json", state)


def _reconciled_state(p: VericodingPaths, phase: str) -> dict[str, Any]:
    _reconcile_candidate_queue_from_ledger(p)
    previous = _read_state(p)
    evidence = _ledger_evidence(
        read_jsonl(p.ledgers_dir / "candidate_bank.jsonl"),
        read_jsonl(p.ledgers_dir / "selector_eval.jsonl"),
        read_jsonl(p.ledgers_dir / "e2e_runs.jsonl"),
        read_jsonl(p.ledgers_dir / "secure_eval.jsonl"),
        read_jsonl(p.ledgers_dir / "adjudications.jsonl"),
        read_jsonl(p.ledgers_dir / "external_guardrail.jsonl"),
        None,
        _read_formal_rows(p),
    )
    state = dict(previous)
    state.update(
        {
            "program_version": RESEARCH_PROGRAM_VERSION,
            "current_phase": phase,
            "phase_status": phase,
            "budget_used": evidence["provider_or_harbor_spend_usd"],
            "live_rows_completed": evidence["live_model_candidate_rows"],
            "provider_calls_completed": evidence["provider_calls_completed"],
            "harbor_jobs_completed": evidence["harbor_completed_external_rows"],
            "semi_formal_rows_completed": evidence["semi_formal_rows"],
            "repair_reevaluations": evidence["repair_reevaluations"],
            "input_tokens": evidence["input_tokens"],
            "output_tokens": evidence["output_tokens"],
            "last_heartbeat_at": now_iso(),
            "last_successful_command": phase,
        }
    )
    if phase in {"complete", "downgraded_complete"}:
        state["next_required_action"] = "none; terminal phase complete"
    return state


def _event(p: VericodingPaths, phase: str, event_type: str, payload: dict[str, Any]) -> None:
    append_jsonl(
        p.ledgers_dir / "phase_events.jsonl",
        [
            {
                "event_id": stable_hash(
                    {"program_version": RESEARCH_PROGRAM_VERSION, "phase": phase, "event": event_type, "payload": payload},
                    length=18,
                ),
                "program_version": RESEARCH_PROGRAM_VERSION,
                "phase": phase,
                "event_type": event_type,
                "payload": payload,
                "created_at": now_iso(),
            }
        ],
    )


def _append_unique(path: Path, rows: list[dict[str, Any]], id_key: str) -> None:
    existing = read_jsonl(path)
    ids = {row[id_key] for row in existing}
    append_jsonl(path, [row for row in rows if row[id_key] not in ids])


def _ledger_has(path: Path, id_key: str, row_id: str) -> bool:
    return any(row.get(id_key) == row_id for row in read_jsonl(path))


def _validate_live_candidate_row(row: dict[str, Any]) -> None:
    if row.get("candidate_source_type") != "live_model":
        return
    if float(row.get("cost_usd") or 0) <= 0:
        raise RuntimeError("live_model candidate row has zero cost")
    if int(row.get("input_tokens") or 0) <= 0 or int(row.get("output_tokens") or 0) <= 0:
        raise RuntimeError("live_model candidate row has zero tokens")
    if float(row.get("wall_seconds") or 0) <= 0:
        raise RuntimeError("live_model candidate row has zero wall time")


def _support_type_candidates(row: dict[str, Any]) -> dict[str, bool]:
    return {
        "hidden_correct": bool(row.get("candidate_label") == "correct"),
        "secure_passing": bool(row.get("security_checks_pass")),
        "regression_clean": bool(row.get("regression_checks_pass")),
    }


def _write_primary_support_ledgers(p: VericodingPaths) -> None:
    candidates = read_jsonl(p.ledgers_dir / "candidate_bank.jsonl")
    selectors = read_jsonl(p.ledgers_dir / "selector_eval.jsonl")
    e2e = read_jsonl(p.ledgers_dir / "e2e_runs.jsonl")
    support_rows = _support_analysis_rows(candidates)
    decomposition_rows = _primary_decomposition_events(candidates, selectors, e2e)
    _append_unique(p.ledgers_dir / "support_analysis.jsonl", support_rows, "support_analysis_row_id")
    _append_unique(p.ledgers_dir / "decomposition_events.jsonl", decomposition_rows, "decomposition_event_id")
    write_csv(p.wrangled_dir / "support_analysis_dev.csv", [r for r in support_rows if r["split"] == "dev"])
    write_csv(
        p.wrangled_dir / "generator_vs_selector_decomposition_dev.csv",
        [r for r in decomposition_rows if r["split"] == "dev"],
    )
    write_csv(p.paper_dir / "tables/candidate_support_by_oracle.csv", _candidate_support_by_oracle(candidates))
    write_csv(p.paper_dir / "tables/candidate_support_by_pool_regime.csv", _candidate_support_by_pool_regime(candidates))


def _support_analysis_rows(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        if row.get("surface") not in PRIMARY_SURFACES:
            continue
        grouped[
            (
                str(row.get("surface")),
                str(row.get("split")),
                str(row.get("task_id")),
                _effective_pool_regime(row),
                str(row.get("oracle_family", "unknown")),
            )
        ].append(row)
    out = []
    for (surface, split, task_id, pool_regime, oracle_family), rows in sorted(grouped.items()):
        out.append(
            {
                "support_analysis_row_id": stable_hash(
                    {
                        "program_version": RESEARCH_PROGRAM_VERSION,
                        "surface": surface,
                        "split": split,
                        "task_id": task_id,
                        "pool_regime": pool_regime,
                        "oracle_family": oracle_family,
                    },
                    length=18,
                ),
                "program_version": RESEARCH_PROGRAM_VERSION,
                "surface": surface,
                "split": split,
                "task_id": task_id,
                "pool_regime": pool_regime,
                "oracle_family": oracle_family,
                "candidate_count": len(rows),
                "has_hidden_correct_support": any(row.get("candidate_label") == "correct" for row in rows),
                "has_secure_passing_support": any(row.get("security_checks_pass") for row in rows),
                "has_regression_clean_support": any(row.get("regression_checks_pass") for row in rows),
                "visible_pass_hidden_fail_count": sum(
                    1 for row in rows if row.get("visible_tests_pass") and not row.get("hidden_tests_pass")
                ),
                "primary_core": True,
                "created_at": now_iso(),
            }
        )
    return out


def _primary_decomposition_events(
    candidates: list[dict[str, Any]],
    selectors: list[dict[str, Any]],
    e2e: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = _generator_vs_selector_failure_decomposition(
        [row for row in candidates if row.get("surface") in PRIMARY_SURFACES],
        selectors,
        e2e,
    )
    out = []
    for row in rows:
        split = str(row.get("split") or "")
        out.append(
            {
                "decomposition_event_id": stable_hash(
                    {
                        "program_version": RESEARCH_PROGRAM_VERSION,
                        "task_id": row["task_id"],
                        "split": split,
                        "failure_class": row["failure_class"],
                    },
                    length=18,
                ),
                "program_version": RESEARCH_PROGRAM_VERSION,
                "split": split,
                "primary_core": True,
                **row,
                "created_at": now_iso(),
            }
        )
    return out


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
        "selector_prompt_version": "observable_baseline_research_v2",
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
        "program_version": RESEARCH_PROGRAM_VERSION,
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
        "selector_cached_input_tokens": meta.get("selector_cached_input_tokens", 0),
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
) -> tuple[dict[str, Any], dict[str, Any]]:
    if pipeline == "single_sample":
        chosen = views[0]
        meta = _zero_selector_meta(pipeline)
    elif pipeline == "best_of_n_random":
        chosen = select_random_observable(views, task_id=task_id)
        meta = _zero_selector_meta(pipeline)
    elif pipeline == "best_of_n_tests_only":
        chosen = select_tests_only_observable(views)
        meta = _zero_selector_meta(pipeline)
    elif pipeline == "best_of_n_structural_only":
        chosen = select_structural_observable(views)
        meta = _zero_selector_meta(pipeline)
    elif pipeline == "best_of_n_llm_judge":
        chosen, meta = select_llm_judge_live(views, task_summary=task_id, model=model)
    else:
        chosen, meta = select_specoracle_live(views, task_summary=task_id, model=model)
    return next(row for row in pool if row["candidate_id"] == chosen.candidate_id), meta


def _task_by_id(p: VericodingPaths, task_id: str) -> dict[str, Any]:
    for task in _load_task_pool(p)["tasks"]:
        if task["task_id"] == task_id:
            return task
    raise KeyError(task_id)


def _candidate_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["surface"], row["split"])
        item = grouped.setdefault(
            key,
            {
                "surface": row["surface"],
                "split": row["split"],
                "rows": 0,
                "live_model_rows": 0,
                "real_harness_rows": 0,
            },
        )
        item["rows"] += 1
        if row.get("candidate_source_type") == "live_model":
            item["live_model_rows"] += 1
        if row.get("surface_evidence_quality") == "real_harness":
            item["real_harness_rows"] += 1
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


def _external_metrics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "rows": len(rows),
            "completed_trials": sum(int(row.get("completed_trials") or 0) for row in rows),
            "harbor_completed_rows": sum(1 for row in rows if int(row.get("completed_trials") or 0) > 0),
        }
    ]


def _formal_slice_metrics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "rows": len(rows),
            "backend": "executable_property_oracle",
            "property_pass_rate": _rate(rows, "property_pass"),
            "visible_property_disagreement_rate": _rate(rows, "visible_property_disagreement"),
        }
    ]


def _write_mechanism_tables(
    p: VericodingPaths,
    candidates: list[dict[str, Any]],
    selectors: list[dict[str, Any]],
    e2e: list[dict[str, Any]],
    adjudications: list[dict[str, Any]],
    formal: list[dict[str, Any]],
) -> None:
    table_dir = p.paper_dir / "tables"
    write_csv(table_dir / "oracle_source_contribution.csv", _oracle_source_contribution(candidates, selectors))
    write_csv(table_dir / "candidate_support_by_pool.csv", _candidate_support_by_pool(candidates))
    write_csv(table_dir / "candidate_support_by_oracle.csv", _candidate_support_by_oracle(candidates))
    write_csv(table_dir / "candidate_support_by_pool_regime.csv", _candidate_support_by_pool_regime(candidates))
    write_csv(table_dir / "support_curves.csv", _support_curves(candidates))
    write_csv(
        table_dir / "generator_vs_selector_failure_decomposition.csv",
        _generator_vs_selector_failure_decomposition(candidates, selectors, e2e),
    )
    write_csv(table_dir / "secure_false_accept_decomposition.csv", _secure_false_accept_decomposition(selectors))
    write_csv(table_dir / "repair_uplift_by_surface.csv", _repair_uplift_by_surface(e2e))
    write_csv(table_dir / "repair_uplift_by_failure_class.csv", _repair_uplift_by_failure_class(adjudications, candidates))
    write_csv(table_dir / "formal_slice_task_inventory.csv", _formal_slice_task_inventory(formal))
    write_csv(table_dir / "formal_slice_selector_metrics.csv", _formal_slice_metrics(formal))
    write_csv(table_dir / "formal_slice_visible_vs_property_disagreement.csv", formal)


def _write_primary_metric_exports(
    p: VericodingPaths,
    candidates: list[dict[str, Any]],
    selectors: list[dict[str, Any]],
    e2e: list[dict[str, Any]],
) -> None:
    primary_candidates = [row for row in candidates if row.get("surface") in PRIMARY_SURFACES]
    primary_selectors = [row for row in selectors if row.get("surface") in PRIMARY_SURFACES]
    primary_e2e = [row for row in e2e if row.get("surface") in PRIMARY_SURFACES]
    write_csv(p.metrics_dir / "primary_core_selector_metrics.csv", _selector_metrics(primary_selectors))
    write_csv(p.metrics_dir / "primary_core_e2e_metrics.csv", _e2e_metrics(primary_e2e))
    write_csv(p.metrics_dir / "primary_core_support_curves.csv", _support_curves(primary_candidates))
    write_csv(p.metrics_dir / "primary_core_disagreement_metrics.csv", _primary_disagreement_metrics(primary_candidates))
    write_csv(
        p.metrics_dir / "primary_core_decomposition.csv",
        _generator_vs_selector_failure_decomposition(primary_candidates, primary_selectors, primary_e2e),
    )
    write_csv(p.wrangled_dir / "internal_hidden_disagreement.csv", _internal_hidden_disagreement(primary_candidates))
    write_csv(p.wrangled_dir / "internal_failure_class_distribution.csv", _internal_failure_class_distribution(primary_candidates))
    write_csv(p.wrangled_dir / "secure_task_discriminability.csv", _secure_task_discriminability(primary_candidates))
    write_csv(p.wrangled_dir / "secure_false_accept_by_selector.csv", _secure_false_accept_decomposition(primary_selectors))
    (p.reports_dir / "internal_visible_vs_hidden_casebook.md").write_text(
        _casebook_markdown("Internal Visible vs Hidden Casebook", _internal_hidden_disagreement(primary_candidates)),
        encoding="utf-8",
    )
    (p.reports_dir / "secure_adversarial_casebook.md").write_text(
        _casebook_markdown("Secure Adversarial Casebook", _secure_task_discriminability(primary_candidates)),
        encoding="utf-8",
    )
    write_csv(p.wrangled_dir / "repair_uplift_dev.csv", _repair_uplift_by_surface([row for row in primary_e2e if row.get("split") == "dev"]))


def _primary_disagreement_metrics(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        grouped[(str(row.get("surface")), str(row.get("split")))].append(row)
    return [
        {
            "surface": surface,
            "split": split,
            "rows": len(rows),
            "visible_pass_hidden_fail_rate": _rate(
                [{"hit": row.get("visible_tests_pass") and not row.get("hidden_tests_pass")} for row in rows],
                "hit",
            ),
            "visible_fail_hidden_pass_rate": _rate(
                [{"hit": (not row.get("visible_tests_pass")) and row.get("hidden_tests_pass")} for row in rows],
                "hit",
            ),
            "visible_pass_secure_fail_rate": _rate(
                [{"hit": row.get("visible_tests_pass") and not row.get("security_checks_pass")} for row in rows],
                "hit",
            ),
        }
        for (surface, split), rows in sorted(grouped.items())
    ]


def _internal_hidden_disagreement(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        if row.get("surface") == "internal":
            grouped[str(row.get("task_id"))].append(row)
    return [
        {
            "task_id": task_id,
            "rows": len(rows),
            "visible_pass_hidden_fail_count": sum(
                1 for row in rows if row.get("visible_tests_pass") and not row.get("hidden_tests_pass")
            ),
            "hidden_correct_count": sum(1 for row in rows if row.get("candidate_label") == "correct"),
            "dominant_harness_status": _dominant_value(rows, "harness_status"),
        }
        for task_id, rows in sorted(grouped.items())
    ]


def _internal_failure_class_distribution(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], int] = defaultdict(int)
    for row in candidates:
        if row.get("surface") != "internal":
            continue
        grouped[(str(row.get("task_id")), _failure_class_for_candidate(row))] += 1
    return [
        {"task_id": task_id, "failure_class": failure_class, "count": count}
        for (task_id, failure_class), count in sorted(grouped.items())
    ]


def _secure_task_discriminability(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        if row.get("surface") == "secure":
            grouped[str(row.get("task_id"))].append(row)
    out = []
    for task_id, rows in sorted(grouped.items()):
        labels = {row.get("candidate_label") for row in rows}
        out.append(
            {
                "task_id": task_id,
                "rows": len(rows),
                "has_secure_pass": any(row.get("security_checks_pass") for row in rows),
                "has_secure_fail": any(not row.get("security_checks_pass") for row in rows),
                "visible_pass_secure_fail_count": sum(
                    1 for row in rows if row.get("visible_tests_pass") and not row.get("security_checks_pass")
                ),
                "discriminative": any(row.get("security_checks_pass") for row in rows)
                and any(not row.get("security_checks_pass") for row in rows),
                "labels": "|".join(sorted(str(label) for label in labels)),
            }
        )
    return out


def _failure_class_for_candidate(row: dict[str, Any]) -> str:
    if not row.get("parse_ok"):
        return "syntax_or_parse_failure"
    if not row.get("visible_tests_pass"):
        return "visible_runtime_or_semantic_failure"
    if not row.get("security_checks_pass"):
        return "security_drift"
    if not row.get("regression_checks_pass"):
        status = str(row.get("harness_status") or "")
        if "state" in status:
            return "state_transition_breakage"
        if "policy" in status or "config" in status:
            return "config_or_policy_mismatch"
        if "edge" in status:
            return "edge_case_omission"
        return "semantic_regression"
    if row.get("candidate_label") == "correct":
        return "correct"
    return "evaluator_ambiguity"


def _casebook_markdown(title: str, rows: list[dict[str, Any]]) -> str:
    lines = [f"# {title}", "", "Generated from primary-core ledger summaries.", ""]
    for row in rows[:20]:
        lines.append(
            "- "
            + ", ".join(f"{key}={value}" for key, value in row.items())
        )
    lines.append("")
    return "\n".join(lines)


def _dominant_value(rows: list[dict[str, Any]], key: str) -> str:
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[str(row.get(key, ""))] += 1
    if not counts:
        return ""
    return max(sorted(counts), key=lambda item: counts[item])


def _oracle_source_contribution(
    candidates: list[dict[str, Any]],
    selectors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_id = {row["candidate_id"]: row for row in candidates}
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in selectors:
        candidate = by_id.get(str(row.get("selected_candidate_id")), {})
        key = (str(row.get("selector_name")), str(candidate.get("oracle_family", "unknown")))
        item = grouped.setdefault(
            key,
            {"selector_name": key[0], "oracle_family": key[1], "selected_rows": 0, "correct_selected": 0},
        )
        item["selected_rows"] += 1
        if row.get("selection_correct"):
            item["correct_selected"] += 1
    for item in grouped.values():
        item["correct_selection_rate"] = round(item["correct_selected"] / item["selected_rows"], 6) if item["selected_rows"] else 0.0
    return list(grouped.values())


def _candidate_support_by_pool(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        grouped[
            (
                str(row.get("surface")),
                str(row.get("split")),
                str(row.get("task_id")),
                _effective_pool_regime(row),
            )
        ].append(row)
    out = []
    for (surface, split, task_id, pool_regime), rows in sorted(grouped.items()):
        out.append(
            {
                "surface": surface,
                "split": split,
                "task_id": task_id,
                "pool_regime": pool_regime,
                "candidate_count": len(rows),
                "has_correct_candidate": any(row.get("candidate_label") == "correct" for row in rows),
                "has_secure_passing_candidate": any(row.get("security_checks_pass") for row in rows),
                "has_regression_clean_candidate": any(row.get("regression_checks_pass") for row in rows),
                "visible_pass_hidden_fail_count": sum(
                    1 for row in rows if row.get("visible_tests_pass") and not row.get("hidden_tests_pass")
                ),
            }
        )
    return out


def _candidate_support_by_oracle(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        if row.get("surface") not in PRIMARY_SURFACES:
            continue
        grouped[
            (
                str(row.get("surface")),
                str(row.get("split")),
                str(row.get("oracle_family", "unknown")),
            )
        ].append(row)
    return [
        _support_summary_row(
            rows,
            {
                "surface": surface,
                "split": split,
                "oracle_family": oracle_family,
            },
        )
        for (surface, split, oracle_family), rows in sorted(grouped.items())
    ]


def _candidate_support_by_pool_regime(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        if row.get("surface") not in PRIMARY_SURFACES:
            continue
        grouped[
            (
                str(row.get("surface")),
                str(row.get("split")),
                _effective_pool_regime(row),
            )
        ].append(row)
    return [
        _support_summary_row(
            rows,
            {
                "surface": surface,
                "split": split,
                "pool_regime": pool_regime,
            },
        )
        for (surface, split, pool_regime), rows in sorted(grouped.items())
    ]


def _support_summary_row(rows: list[dict[str, Any]], base: dict[str, Any]) -> dict[str, Any]:
    task_ids = {row.get("task_id") for row in rows}
    return {
        **base,
        "rows": len(rows),
        "tasks": len(task_ids),
        "hidden_correct_support_rate": _task_support_rate(rows, "hidden_correct"),
        "secure_passing_support_rate": _task_support_rate(rows, "secure_passing"),
        "regression_clean_support_rate": _task_support_rate(rows, "regression_clean"),
        "visible_pass_hidden_fail_count": sum(
            1 for row in rows if row.get("visible_tests_pass") and not row.get("hidden_tests_pass")
        ),
    }


def _task_support_rate(rows: list[dict[str, Any]], support_key: str) -> float:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("task_id"))].append(row)
    if not grouped:
        return 0.0
    hits = 0
    for task_rows in grouped.values():
        if any(_row_support(row).get(support_key) for row in task_rows):
            hits += 1
    return round(hits / len(grouped), 6)


def _row_support(row: dict[str, Any]) -> dict[str, bool]:
    support = row.get("support_type_candidates")
    if isinstance(support, dict):
        return {
            "hidden_correct": bool(support.get("hidden_correct")),
            "secure_passing": bool(support.get("secure_passing")),
            "regression_clean": bool(support.get("regression_clean")),
        }
    return _support_type_candidates(row)


def _support_curves(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        grouped[(str(row.get("surface")), str(row.get("split")), str(row.get("task_id")))].append(row)
    rows_out = []
    for (surface, split, task_id), rows in sorted(grouped.items()):
        ordered = sorted(rows, key=lambda row: int(row.get("seed") or 0))
        for n in range(1, len(ordered) + 1):
            prefix = ordered[:n]
            rows_out.append(
                {
                    "surface": surface,
                    "split": split,
                    "task_id": task_id,
                    "pool_size": n,
                    "has_correct_candidate": any(row.get("candidate_label") == "correct" for row in prefix),
                    "has_nonfalse_accept_candidate": any(_final_success(row) for row in prefix),
                    "oracle_families_seen": len({row.get("oracle_family", "unknown") for row in prefix}),
                }
            )
    return rows_out


def _generator_vs_selector_failure_decomposition(
    candidates: list[dict[str, Any]],
    selectors: list[dict[str, Any]],
    e2e: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped_candidates: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        grouped_candidates[
            (
                str(row.get("split")),
                str(row.get("surface")),
                str(row.get("task_id")),
            )
        ].append(row)
    selector_by_task = {
        (row.get("split"), row["task_id"]): row
        for row in selectors
        if row.get("selector_name") == "specoracle_selector"
    }
    e2e_by_task = {
        (row.get("split"), row["task_id"]): row
        for row in e2e
        if row.get("pipeline_name") == "best_of_n_specoracle_plus_one_repair"
    }
    out = []
    for (split, surface, task_id), pool in sorted(grouped_candidates.items()):
        has_correct = any(row.get("candidate_label") == "correct" for row in pool)
        selector_row = selector_by_task.get((split, task_id), {})
        e2e_row = e2e_by_task.get((split, task_id), {})
        if not has_correct:
            failure_class = "no_correct_candidate_in_pool"
        elif not selector_row.get("selection_correct"):
            failure_class = "selector_missed_supported_pool"
        elif selector_row.get("selection_correct") and not e2e_row.get("final_success", False):
            failure_class = "repair_or_pipeline_failed_after_selection"
        else:
            failure_class = "supported_success"
        out.append(
            {
                "split": split,
                "surface": surface,
                "task_id": task_id,
                "candidate_pool_size": len(pool),
                "has_correct_candidate": has_correct,
                "specoracle_selection_correct": bool(selector_row.get("selection_correct")),
                "specoracle_plus_repair_success": bool(e2e_row.get("final_success")),
                "failure_class": failure_class,
            }
        )
    return out


def _secure_false_accept_decomposition(selectors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in selectors:
        if row.get("surface") == "secure" and row.get("split") == "confirmatory":
            grouped[str(row.get("selector_name"))].append(row)
    return [
        {
            "selector_name": selector,
            "rows": len(rows),
            "false_accept_rate": _rate(rows, "false_accept"),
            "secure_false_accept_rate": _rate(rows, "secure_false_accept"),
        }
        for selector, rows in sorted(grouped.items())
    ]


def _repair_uplift_by_surface(e2e: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in e2e:
        grouped[str(row.get("surface"))][str(row.get("pipeline_name"))].append(row)
    out = []
    for surface, by_pipeline in sorted(grouped.items()):
        no_repair = _rate(by_pipeline.get("best_of_n_specoracle", []), "final_success")
        one_repair = _rate(by_pipeline.get("best_of_n_specoracle_plus_one_repair", []), "final_success")
        out.append(
            {
                "surface": surface,
                "no_repair_success_rate": no_repair,
                "one_repair_success_rate": one_repair,
                "repair_uplift": round(one_repair - no_repair, 6),
            }
        )
    return out


def _repair_uplift_by_failure_class(
    adjudications: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_candidate = {row["candidate_id"]: row for row in candidates}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in adjudications:
        original = by_candidate.get(str(row.get("selected_candidate_id")), {})
        grouped[str(original.get("candidate_label", "unknown"))].append(row)
    return [
        {
            "original_candidate_label": label,
            "repair_rows": len(rows),
            "repair_success_rate": _rate(
                [
                    {"success": (row.get("reevaluation_results") or {}).get("candidate_label") == "correct"}
                    for row in rows
                ],
                "success",
            ),
        }
        for label, rows in sorted(grouped.items())
    ]


def _formal_slice_task_inventory(formal: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in formal:
        grouped[str(row.get("task_id"))].append(row)
    return [
        {
            "task_id": task_id,
            "rows": len(rows),
            "backend": "executable_property_oracle",
            "visible_property_disagreement_count": sum(1 for row in rows if row.get("visible_property_disagreement")),
        }
        for task_id, rows in sorted(grouped.items())
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
        for surface, quota in RESEARCH_LIVE_QUOTAS.items()
    )


def _surface_summary(
    candidates: list[dict[str, Any]],
    selectors: list[dict[str, Any]],
    e2e: list[dict[str, Any]],
    external: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    surfaces = sorted({row["surface"] for row in candidates} | {"terminalbench_guardrail"})
    return [
        {
            "surface": surface,
            "candidate_rows": sum(1 for row in candidates if row["surface"] == surface),
            "real_harness_rows": sum(
                1
                for row in candidates
                if row["surface"] == surface and row.get("surface_evidence_quality") == "real_harness"
            ),
            "selector_rows": sum(1 for row in selectors if row["surface"] == surface),
            "e2e_rows": sum(1 for row in e2e if row["surface"] == surface),
            "external_guardrail_rows": len(external) if surface == "terminalbench_guardrail" else 0,
        }
        for surface in surfaces
    ]


def _failure_taxonomy(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], int] = defaultdict(int)
    for row in candidates:
        grouped[(row["surface"], row["candidate_label"], row.get("harness_status", ""))] += 1
    return [
        {"surface": surface, "candidate_label": label, "harness_status": status, "count": count}
        for (surface, label, status), count in sorted(grouped.items())
    ]


def _budget_summary(
    candidates: list[dict[str, Any]],
    selectors: list[dict[str, Any]],
    e2e: list[dict[str, Any]],
    adjudications: list[dict[str, Any]],
    external: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    e2e_selection_cost = sum(float(row.get("cost_usd") or 0) for row in e2e)
    repair_cost = sum(float(row.get("incremental_cost_usd") or 0) for row in adjudications)
    return [
        {"phase": "candidate_generation", "cost_usd": sum(float(row.get("cost_usd") or 0) for row in candidates)},
        {"phase": "selector_eval", "cost_usd": sum(float(row.get("selector_cost_usd") or 0) for row in selectors)},
        {"phase": "e2e_repair", "cost_usd": e2e_selection_cost + repair_cost},
        {"phase": "adjudication", "cost_usd": 0.0},
        {"phase": "external_harbor", "cost_usd": sum(float(row.get("cost_usd") or 0) for row in external)},
    ]


def _enforce_phase_budget(p: VericodingPaths, phase: str) -> None:
    candidates = read_jsonl(p.ledgers_dir / "candidate_bank.jsonl")
    selectors = read_jsonl(p.ledgers_dir / "selector_eval.jsonl")
    e2e = read_jsonl(p.ledgers_dir / "e2e_runs.jsonl")
    adjudications = read_jsonl(p.ledgers_dir / "adjudications.jsonl")
    external = read_jsonl(p.ledgers_dir / "external_guardrail.jsonl")
    spent = {row["phase"]: float(row["cost_usd"]) for row in _budget_summary(candidates, selectors, e2e, adjudications, external)}
    if phase in RESEARCH_PHASE_BUDGETS and spent.get(phase, 0.0) > RESEARCH_PHASE_BUDGETS[phase]:
        raise RuntimeError(f"{phase} phase budget exceeded: {spent[phase]:.4f} > {RESEARCH_PHASE_BUDGETS[phase]:.4f}")
    total = sum(spent.values())
    gate = spend_gate(total, claim_movement_visible=_claim_movement_visible(p))
    if gate["review_required"]:
        raise RuntimeError(gate["stop_reason"])


def _ledger_evidence(
    candidates: list[dict[str, Any]],
    selectors: list[dict[str, Any]],
    e2e: list[dict[str, Any]],
    secure: list[dict[str, Any]],
    adjudications: list[dict[str, Any]],
    external: list[dict[str, Any]],
    started_monotonic: float | None,
    formal: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    live = [row for row in candidates if row.get("candidate_source_type") == "live_model"]
    total_spend = sum(float(row.get("cost_usd") or 0) for row in candidates)
    total_spend += sum(float(row.get("selector_cost_usd") or 0) for row in selectors)
    total_spend += sum(float(row.get("cost_usd") or 0) for row in e2e)
    total_spend += sum(float(row.get("incremental_cost_usd") or 0) for row in adjudications)
    total_spend += sum(float(row.get("cost_usd") or 0) for row in external)
    input_tokens = sum(int(row.get("input_tokens") or 0) for row in candidates)
    input_tokens += sum(int(row.get("selector_input_tokens") or 0) for row in selectors)
    input_tokens += sum(int(row.get("input_tokens") or 0) for row in e2e)
    input_tokens += sum(int(row.get("input_tokens") or 0) for row in adjudications)
    output_tokens = sum(int(row.get("output_tokens") or 0) for row in candidates)
    output_tokens += sum(int(row.get("selector_output_tokens") or 0) for row in selectors)
    output_tokens += sum(int(row.get("output_tokens") or 0) for row in e2e)
    output_tokens += sum(int(row.get("output_tokens") or 0) for row in adjudications)
    provider_calls = len(live)
    provider_calls += sum(1 for row in selectors if float(row.get("selector_cost_usd") or 0) > 0)
    provider_calls += sum(1 for row in e2e if float(row.get("cost_usd") or 0) > 0)
    provider_calls += len(adjudications)
    runtime = round((time.monotonic() - started_monotonic) if started_monotonic else 0, 3)
    return {
        "live_model_candidate_rows": len(live),
        "provider_or_harbor_spend_usd": round(total_spend, 6),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "supervised_runtime_seconds": runtime,
        "repair_reevaluations": len(adjudications),
        "harbor_completed_external_rows": sum(1 for row in external if int(row.get("completed_trials") or 0) > 0),
        "semi_formal_rows": len(formal or []),
        "provider_calls_completed": provider_calls,
        "real_harness_candidate_rows": sum(1 for row in candidates if row.get("surface_evidence_quality") == "real_harness"),
        "surface_quotas_met": _surface_quotas_met(candidates),
    }


def _conference_claim_movement(
    candidates: list[dict[str, Any]],
    selectors: list[dict[str, Any]],
    e2e: list[dict[str, Any]],
    secure: list[dict[str, Any]],
    formal: list[dict[str, Any]],
) -> dict[str, Any]:
    support_rows = _candidate_support_by_pool(candidates)
    oracle_families = {row.get("oracle_family") for row in candidates if row.get("oracle_family")}
    mixed_support = any(
        row.get("has_correct_candidate") and "mixed" in str(row.get("pool_regime", "")) for row in support_rows
    )
    visible_hidden_disagreement = any(
        row.get("visible_tests_pass") and not row.get("hidden_tests_pass") for row in candidates
    )
    selector_metrics = _selector_metrics(selectors)
    e2e_metrics = _e2e_metrics(e2e)
    selector_movement = _claim_movement(selector_metrics, e2e_metrics, _secure_metrics(secure))
    secure_table = _secure_false_accept_decomposition(selectors)
    secure_by_selector = {row["selector_name"]: row for row in secure_table}
    spec_secure = secure_by_selector.get("specoracle_selector", {})
    tests_secure = secure_by_selector.get("tests_only_selector", {})
    structural_secure = secure_by_selector.get("structural_selector", {})
    secure_reduced = bool(secure) and float(spec_secure.get("secure_false_accept_rate", 1.0)) < min(
        float(tests_secure.get("secure_false_accept_rate", 1.0)),
        float(structural_secure.get("secure_false_accept_rate", 1.0)),
    )
    repair_rows = _repair_uplift_by_surface(e2e)
    return {
        "claim_1_oracle_support_headroom": len(oracle_families) >= 3 and mixed_support,
        "claim_2_visible_hidden_disagreement": visible_hidden_disagreement and len(formal) >= 5,
        "claim_3_ranking_support_mechanism": bool(selector_movement.get("claim_1_selector_beats_baselines"))
        and any(row.get("failure_class") == "no_correct_candidate_in_pool" for row in _generator_vs_selector_failure_decomposition(candidates, selectors, e2e)),
        "claim_4_secure_false_accept_reduced": secure_reduced,
        "claim_5_repair_uplift": any(float(row.get("repair_uplift") or 0) > 0 for row in repair_rows),
    }


def _claim_movement(
    selector_metrics: list[dict[str, Any]],
    e2e_metrics: list[dict[str, Any]],
    secure_metrics: list[dict[str, Any]],
) -> dict[str, Any]:
    spec = _metric(selector_metrics, "confirmatory", "specoracle_selector", "selector_name")
    tests = _metric(selector_metrics, "confirmatory", "tests_only_selector", "selector_name")
    structural = _metric(selector_metrics, "confirmatory", "structural_selector", "selector_name")
    spec_e2e = _metric(e2e_metrics, "confirmatory", "best_of_n_specoracle", "pipeline_name")
    single = _metric(e2e_metrics, "confirmatory", "single_sample", "pipeline_name")
    secure = secure_metrics[0] if secure_metrics else {}
    return {
        "claim_1_selector_beats_baselines": float(spec.get("top1_accuracy", 0)) > max(
            float(tests.get("top1_accuracy", 0)), float(structural.get("top1_accuracy", 0))
        ),
        "claim_2_e2e_beats_single": float(spec_e2e.get("final_success_rate", 0)) > float(single.get("final_success_rate", 0)),
        "claim_4_secure_false_accept_reduced": float(secure.get("hidden_pass_rate", 0)) > 0,
    }


def _claim_movement_visible(p: VericodingPaths) -> bool:
    if not (p.metrics_dir / "selector_metrics.csv").exists():
        return False
    selectors = read_jsonl(p.ledgers_dir / "selector_eval.jsonl")
    e2e = read_jsonl(p.ledgers_dir / "e2e_runs.jsonl")
    secure = read_jsonl(p.ledgers_dir / "secure_eval.jsonl")
    movement = _claim_movement(_selector_metrics(selectors), _e2e_metrics(e2e), _secure_metrics(secure))
    return any(bool(value) for value in movement.values())


def _metric(rows: list[dict[str, Any]], split: str, name: str, name_key: str) -> dict[str, Any]:
    for row in rows:
        if row.get("split") == split and row.get(name_key) == name:
            return row
    return {}


def _run_success_contract(p: VericodingPaths) -> bool:
    required = [
        p.ledgers_dir / "candidate_bank.jsonl",
        p.ledgers_dir / "selector_eval.jsonl",
        p.ledgers_dir / "e2e_runs.jsonl",
        p.ledgers_dir / "secure_eval.jsonl",
        p.ledgers_dir / "external_guardrail.jsonl",
        p.ledgers_dir / "formal_slice_eval.jsonl",
        p.ledgers_dir / "adjudications.jsonl",
        p.reports_dir / "final_synthesis.md",
        p.root / "CLAIMS.md",
    ]
    if not all(path.exists() and path.read_text(encoding="utf-8").strip() for path in required):
        return False
    candidates = read_jsonl(p.ledgers_dir / "candidate_bank.jsonl")
    selectors = read_jsonl(p.ledgers_dir / "selector_eval.jsonl")
    e2e = read_jsonl(p.ledgers_dir / "e2e_runs.jsonl")
    secure = read_jsonl(p.ledgers_dir / "secure_eval.jsonl")
    external = read_jsonl(p.ledgers_dir / "external_guardrail.jsonl")
    formal = _read_formal_rows(p)
    adjudications = read_jsonl(p.ledgers_dir / "adjudications.jsonl")
    evidence = _ledger_evidence(candidates, selectors, e2e, secure, adjudications, external, None, formal)
    return bool(
        evidence["live_model_candidate_rows"] > 0
        and evidence["provider_calls_completed"] > 0
        and evidence["repair_reevaluations"] > 0
        and evidence["harbor_completed_external_rows"] > 0
        and evidence["semi_formal_rows"] > 0
        and len(selectors) > 0
        and len(e2e) > 0
        and len(secure) > 0
    )


def _write_claims(p: VericodingPaths, claims: list[dict[str, Any]]) -> None:
    lines = ["# Vericoding Research v2 Claims", ""]
    for claim in claims:
        lines.extend([f"## {claim['claim_id']}", "", f"- Status: `{claim['status']}`", f"- Floor gated: `{claim['floor_gated']}`", f"- Claim: {claim['claim']}", ""])
    (p.root / "CLAIMS.md").write_text("\n".join(lines), encoding="utf-8")


def _write_final_synthesis(
    p: VericodingPaths,
    evidence: dict[str, Any],
    floors: dict[str, Any],
    claims: list[dict[str, Any]],
) -> None:
    lines = [
        "# Vericoding Research v2 Final Synthesis",
        "",
        "This synthesis is derived from conference-program ledgers under `runs/vericoding_research_v2/`.",
        "",
        "## Evidence",
        "",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in evidence.items())
    lines.extend(["", "## Floors", ""])
    lines.append(f"- Program floors met: `{floors['program_floors_met']}`")
    for key, check in floors["checks"].items():
        lines.append(f"- {key}: `{check['observed']}` / `{check['floor']}` met=`{check['met']}`")
    lines.extend(["", "## Claims", ""])
    lines.extend(f"- {claim['claim_id']}: `{claim['status']}`" for claim in claims)
    (p.reports_dir / "final_synthesis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _pilot_gate_report(p: VericodingPaths) -> dict[str, Any]:
    candidates = read_jsonl(p.ledgers_dir / "candidate_bank.jsonl")
    dev = [row for row in candidates if row.get("split") == "dev"]
    by_surface: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in dev:
        by_surface[row["surface"]].append(row)
    checks = {
        "internal": _has_internal_disagreement(by_surface.get("internal", [])),
        "secure": _has_pass_and_fail(by_surface.get("secure", []), require_real=True),
    }
    report = {
        "program_version": RESEARCH_PROGRAM_VERSION,
        "created_at": now_iso(),
        "checks": checks,
        "pilot_passed": all(checks.values()),
        "failed_surfaces": [surface for surface, passed in checks.items() if not passed],
        "scope": "primary_core_only",
        "secondary_transfer_deferred": True,
        "tertiary_external_deferred": True,
    }
    write_json(p.reports_dir / "pilot_gate_report.json", report)
    _write_report(
        p,
        "pilot_gate_report.md",
        "Discriminability Pilot Gate",
        [
            "Scope: `primary_core_only`",
            *[f"{surface}: `{passed}`" for surface, passed in checks.items()],
            "SCBench transfer and Terminal-Bench external validity are deferred to explicit later commands.",
        ],
    )
    return report


def _has_label_disagreement(rows: list[dict[str, Any]], *, require_real: bool) -> bool:
    if require_real and not any(row.get("surface_evidence_quality") == "real_harness" for row in rows):
        return False
    return len({row.get("candidate_label") for row in rows}) >= 2


def _has_internal_disagreement(rows: list[dict[str, Any]]) -> bool:
    real_rows = [row for row in rows if row.get("surface_evidence_quality") == "real_harness"]
    if not real_rows:
        return False
    if len({row.get("candidate_label") for row in real_rows}) >= 2:
        return True
    return any(row.get("visible_tests_pass") and not row.get("hidden_tests_pass") for row in real_rows)


def _has_pass_and_fail(rows: list[dict[str, Any]], *, require_real: bool) -> bool:
    if require_real and not any(row.get("surface_evidence_quality") == "real_harness" for row in rows):
        return False
    labels = {row.get("candidate_label") for row in rows}
    return "correct" in labels and len(labels - {"correct"}) >= 1


def _queue_counts(p: VericodingPaths) -> dict[str, int]:
    path = p.state_dir / "task_queue.json"
    if not path.exists():
        return {}
    queue = read_json(path)
    counts: dict[str, int] = defaultdict(int)
    for item in queue.get("items", []):
        counts[item["status"]] += 1
    return dict(counts)


def _parse_iso(value: str) -> datetime:
    text = value.replace("Z", "+00:00")
    return datetime.fromisoformat(text)


def _git_ignored(path: str) -> bool:
    completed = subprocess.run(["git", "check-ignore", "-q", path], check=False)
    return completed.returncode == 0
