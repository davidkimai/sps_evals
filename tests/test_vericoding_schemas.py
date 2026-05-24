from __future__ import annotations

from pathlib import Path

from specoracle.vericoding.schemas import (
    PROGRAM_VERSION,
    CandidateBankRow,
    append_jsonl,
    now_iso,
    read_jsonl,
    stable_hash,
    validate_dataclass_row,
)


def test_candidate_bank_schema_round_trip(tmp_path: Path) -> None:
    row = CandidateBankRow(
        program_version=PROGRAM_VERSION,
        bank_row_id="row1",
        surface="secure",
        split="dev",
        task_id="safe_path_validation",
        stable_sample_id="vericoding:secure:dev:safe_path_validation",
        candidate_id="c1",
        candidate_source="reference_oracle",
        candidate_lineage="fixture",
        generator_condition="spec_conditioned_prompt",
        generator_model="deterministic-fixture",
        prompt_template_version="v1",
        temperature=None,
        seed=1,
        raw_artifact_policy="tracked_generated_candidate_no_external_raw_prompt",
        candidate_artifact_path="candidate.py",
        candidate_sha256="sha",
        visible_compile_pass=True,
        visible_tests_pass=True,
        hidden_tests_pass=True,
        property_checks_pass=True,
        regression_checks_pass=True,
        security_checks_pass=True,
        parse_ok=True,
        cc_average=1.0,
        max_nesting_depth=1,
        maintainability_index=90.0,
        redundancy_score=0.0,
        candidate_label="correct",
        deceptive_candidate=False,
        insecure_candidate=False,
        regression_candidate=False,
        cost_usd=0.0,
        input_tokens=0,
        output_tokens=0,
        runner_git_commit="abc",
        runner_git_dirty=False,
        created_at=now_iso(),
    )
    validate_dataclass_row(row)
    path = tmp_path / "ledger.jsonl"
    append_jsonl(path, [row.__dict__])

    loaded = read_jsonl(path)

    assert loaded[0]["stable_sample_id"] == "vericoding:secure:dev:safe_path_validation"
    assert stable_hash({"a": 1}) == stable_hash({"a": 1})
