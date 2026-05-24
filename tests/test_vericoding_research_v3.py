from __future__ import annotations

from pathlib import Path

from specoracle.vericoding.research_program_v3 import (
    FRESH_HARBOR_ROW_FLOOR,
    PRIMARY_CONFIRMATORY_TARGET,
    PRIMARY_DEV_TARGET,
    PRIMARY_TASK_TARGET,
    build_completion_contract,
    bootstrap,
    paths,
    triage_decision_for_candidate,
)
from specoracle.vericoding.schemas import append_jsonl, read_json
from specoracle.vericoding import live_generation
from specoracle.vericoding.live_selection import (
    SelectorDecisionError,
    _parse_decision,
    observable_views,
)


def test_v3_bootstrap_clears_launch_blockers_without_conference_completion(tmp_path: Path) -> None:
    root = tmp_path / "research_v3"

    contract = bootstrap(root)

    assert contract["launch_blockers"] == []
    assert contract["worldview_grounded"] is True
    assert contract["primary_denominator_frozen"] is True
    assert contract["trust_boundary_artifacts_complete"] is True
    assert contract["narrow_waist_suite_frozen"] is True
    assert contract["artifact_complete"] is True
    assert contract["backbone_complete"] is False
    assert contract["conference_complete"] is False
    assert "inspect_claim_logs_present" in contract["conference_blockers"]

    primary = read_json(root / "manifests" / "primary_core_task_pool.json")
    dev = read_json(root / "manifests" / "primary_core_dev_manifest.json")
    confirm = read_json(root / "manifests" / "primary_core_confirmatory_manifest.json")

    assert primary["task_count"] == PRIMARY_TASK_TARGET
    assert dev["task_count"] == PRIMARY_DEV_TARGET
    assert confirm["task_count"] == PRIMARY_CONFIRMATORY_TARGET
    assert (root / "PRIMARY_CLAIM_LOCK.md").exists()
    assert (root / "reports" / "worldview_delta_after_apart_grounding.md").exists()
    assert (root / "trust_boundary_manifest.json").exists()
    assert (root / "must_review_artifacts.csv").exists()
    assert (root / "assumption_surface.csv").exists()
    assert (root / "verification_facade_casebook.md").exists()
    assert (root / "reports" / "phase_minus_1_grounding.md").exists()
    assert (root / "reports" / "prompt_provenance_policy.md").exists()
    assert (root / "reports" / "evidence_truth_layers.md").exists()
    assert (root / "state" / "grounding_complete.json").exists()
    assert (root / "state" / "triage_policy_freeze.json").exists()
    assert (root / "state" / "identity_schema_freeze.json").exists()
    assert (root / "manifests" / "owned_expansion_manifest.json").exists()

    grounding = read_json(root / "state" / "grounding_complete.json")
    assert grounding["ready_for_code_changes"] is True

    expansion = read_json(root / "manifests" / "owned_expansion_manifest.json")
    assert expansion["task_count"] == 24
    role_counts = {}
    for task in expansion["tasks"]:
        role_counts[task["expansion_role"]] = role_counts.get(task["expansion_role"], 0) + 1
        assert task["primary_denominator"] is False
    assert role_counts == {
        "secure_breadth": 8,
        "ambiguity_review_heavy": 6,
        "negative_control_low_review_risk": 6,
        "hard_support_generation_stress": 4,
    }


def test_v3_completion_thresholds_do_not_accept_one_external_row(tmp_path: Path) -> None:
    root = tmp_path / "research_v3"
    bootstrap(root)
    p = paths(root)

    append_jsonl(
        p.ledgers_dir / "external_guardrail.jsonl",
        [{"fresh_v3_harbor_backed": True, "task_id": "external-demo", "completed_trials": 1}],
    )

    contract = build_completion_contract(p)

    assert contract["observed"]["fresh_v3_harbor_rows"] == 1
    assert contract["fresh_external_slice_sufficient"] is False
    assert contract["thresholds"]["fresh_external_slice_sufficient"]["fresh_harbor_backed_rows"] == FRESH_HARBOR_ROW_FLOOR
    assert contract["conference_complete"] is False


def test_v3_secure_rejection_requires_challenge_rows_and_tests_only_false_accept(tmp_path: Path) -> None:
    root = tmp_path / "research_v3"
    bootstrap(root)
    p = paths(root)

    append_jsonl(
        p.ledgers_dir / "candidate_bank.jsonl",
        [
                {
                    "surface": "secure",
                    "split": "confirmatory",
                    "task_id": f"secure-{idx}",
                    "visible_tests_pass": True,
                    "security_checks_pass": False,
                    "claim_bearing": True,
                    "evaluation_mode": "real_harness",
                    "fallback_used": False,
                    "candidate_source_type": "live_model",
                    "surface_evidence_quality": "real_harness",
                }
                for idx in range(4)
            ],
    )
    contract_without_selector = build_completion_contract(p)
    assert contract_without_selector["secure_rejection_testable"] is False

    append_jsonl(
        p.ledgers_dir / "selector_eval.jsonl",
        [
            {
                "selector_name": "tests_only_selector",
                "secure_false_accept": True,
                "claim_bearing": True,
                "selector_parse_failed": False,
                "selector_view": "anonymized_claim_bearing",
            }
        ],
    )
    contract = build_completion_contract(p)
    assert contract["secure_rejection_testable"] is True


def test_v3_support_mechanism_threshold_uses_observed_confirmatory_support(tmp_path: Path) -> None:
    root = tmp_path / "research_v3"

    contract = bootstrap(root)

    assert contract["support_mechanism_testable"] is False
    assert contract["observed"]["confirmatory_support_present_tasks"] >= 4
    assert contract["observed"]["confirmatory_support_absent_tasks"] >= 4
    assert contract["observed"]["observed_confirmatory_support_present_tasks"] == 0


def test_v3_completion_ignores_canary_or_proxy_rows(tmp_path: Path) -> None:
    root = tmp_path / "research_v3"
    bootstrap(root)
    p = paths(root)

    append_jsonl(
        p.ledgers_dir / "candidate_bank.jsonl",
        [
            {
                "claim_bearing": True,
                "evaluation_mode": "proxy",
                "fallback_used": False,
                "candidate_source_type": "live_model",
                "surface_evidence_quality": "proxy_heuristic",
            },
            {
                "claim_bearing": True,
                "evaluation_mode": "real_harness",
                "fallback_used": False,
                "candidate_source_type": "v3_controlled_agent_canary",
                "surface_evidence_quality": "real_harness",
            },
        ],
    )

    contract = build_completion_contract(p)

    assert contract["observed"]["claim_bearing_candidate_rows"] == 0
    assert contract["observed"]["excluded_canary_or_nonclaim_candidate_rows"] == 2
    assert contract["conference_complete"] is False


def test_claim_bearing_generation_rejects_proxy_and_uses_visible_secure_specs() -> None:
    task = {
        "surface": "secure",
        "split": "dev",
        "task_id": "safe_path_validation",
        "stable_sample_id": "sample",
    }

    try:
        live_generation.generate_live_candidate(
            task,
            condition="baseline_prompt",
            sample_index=0,
            model="mock",
            artifact_dir=Path("/tmp/unused"),
            provenance={"runner_git_commit": "", "runner_git_dirty": False, "diff_fingerprint": "", "dirty_override": False},
            claim_bearing=True,
            evaluation_mode="proxy",
        )
    except ValueError as exc:
        assert "real_harness" in str(exc)
    else:
        raise AssertionError("claim-bearing proxy generation should fail before provider call")

    summary = live_generation._task_summary(task)
    provenance = live_generation.prompt_provenance_for_task(task)

    assert "solution_safe_path_validation" in summary
    assert "rm -rf" not in summary
    assert "../secret" not in summary
    assert provenance["hidden_evaluator_sources_used"] == []
    assert "data/vericoding_visible_secure_specs.json" in provenance["allowed_prompt_sources"]
    assert "src/specoracle/vericoding/hidden_oracles.py" in provenance["forbidden_prompt_sources"]


def test_selector_claim_bearing_parse_failure_does_not_default_to_first_candidate() -> None:
    try:
        _parse_decision(
            "{}",
            ["candidate_1", "candidate_2"],
            allow_default=False,
            chosen_key="chosen_candidate",
        )
    except SelectorDecisionError:
        pass
    else:
        raise AssertionError("claim-bearing selector parse failure should not default to candidate_1")


def test_claim_bearing_selector_view_excludes_source_and_lineage_fields() -> None:
    rows = [
        {
            "candidate_id": "task:zen:live0",
            "task_id": "task",
            "surface": "internal",
            "split": "confirmatory",
            "stable_sample_id": "stable",
            "candidate_source_type": "live_model",
            "candidate_source": "openai_responses",
            "generator_condition": "zen",
            "candidate_sha256": "sha",
            "code_summary": "def solve(): pass",
            "visible_compile_pass": True,
            "visible_tests_pass": True,
            "visible_proxy_checks_pass": True,
            "visible_regression_proxy_pass": True,
            "visible_security_proxy_pass": True,
            "parse_ok": True,
        }
    ]
    view = observable_views(rows)[0]
    payload = view.to_claim_bearing_selector_dict(candidate_handle="candidate_1")

    assert payload["candidate_handle"] == "candidate_1"
    assert "candidate_id" not in payload
    assert "candidate_source" not in payload
    assert "candidate_source_type" not in payload
    assert "generator_condition" not in payload


def test_triage_policy_maps_selected_artifacts() -> None:
    good = {
        "parse_ok": True,
        "visible_tests_pass": True,
        "hidden_tests_pass": True,
        "security_checks_pass": True,
        "regression_checks_pass": True,
    }
    hidden_fail = {**good, "hidden_tests_pass": False}

    assert triage_decision_for_candidate(good) == ("auto_accept", "all_executable_and_review_gates_passed")
    assert triage_decision_for_candidate(good, review_boundary_blocker=True) == (
        "escalate_to_review",
        "review_boundary_blocker",
    )
    assert triage_decision_for_candidate(hidden_fail) == ("auto_reject", "hidden_executable_failure")
