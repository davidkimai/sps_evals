from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict, dataclass, fields
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

PROGRAM_VERSION = "vericoding_depth_v1"
SCHEMA_VERSION = "vericoding_depth_schema_v1"
SELECTOR_PROMPT_VERSION = "specoracle_selector_v1"
GENERATION_PROMPT_VERSION = "vericoding_generation_v1"
REPAIR_PROMPT_VERSION = "cegis_lite_repair_v1"
DEFAULT_ROOT = Path("runs/vericoding_depth_v1")
LIVE_PROGRAM_VERSION = "vericoding_depth_v2"
LIVE_DEFAULT_ROOT = Path("runs/vericoding_depth_v2")

Surface = Literal["internal", "scbench_regression", "terminalbench_guardrail", "secure"]
Split = Literal["dev", "confirmatory"]
TriageDecision = Literal["auto_accept", "auto_reject", "escalate_to_review"]
ClaimStatus = Literal["success", "partial", "null", "unsupported"]
CandidateLabel = Literal[
    "correct",
    "plausible_wrong",
    "regression_fail",
    "security_fail",
    "syntax_fail",
    "runtime_fail",
    "infra_fail",
]

VALID_LABELS: tuple[str, ...] = (
    "correct",
    "plausible_wrong",
    "regression_fail",
    "security_fail",
    "syntax_fail",
    "runtime_fail",
    "infra_fail",
)


@dataclass(frozen=True)
class VericodingPaths:
    root: Path = DEFAULT_ROOT

    @property
    def config_dir(self) -> Path:
        return self.root / "config"

    @property
    def manifests_dir(self) -> Path:
        return self.root / "manifests"

    @property
    def ledgers_dir(self) -> Path:
        return self.root / "ledgers"

    @property
    def wrangled_dir(self) -> Path:
        return self.root / "data" / "wrangled"

    @property
    def metrics_dir(self) -> Path:
        return self.root / "metrics"

    @property
    def reports_dir(self) -> Path:
        return self.root / "reports"

    @property
    def paper_dir(self) -> Path:
        return self.root / "paper_artifacts"

    @property
    def state_dir(self) -> Path:
        return self.root / "state"


@dataclass(frozen=True)
class TaskRecord:
    program_version: str
    surface: Surface
    split: Split
    task_id: str
    stable_sample_id: str
    role: str
    source_ref: str
    task_hash: str
    raw_content_committed: bool
    regression_sensitive: bool
    security_relevant: bool
    external_surface: bool


@dataclass(frozen=True)
class CandidateBankRow:
    program_version: str
    bank_row_id: str
    surface: Surface
    split: Split
    task_id: str
    stable_sample_id: str
    candidate_id: str
    candidate_source: str
    candidate_lineage: str
    generator_condition: str
    generator_model: str
    prompt_template_version: str
    temperature: float | None
    seed: int | None
    raw_artifact_policy: str
    candidate_artifact_path: str
    candidate_sha256: str
    visible_compile_pass: bool
    visible_tests_pass: bool
    hidden_tests_pass: bool
    property_checks_pass: bool
    regression_checks_pass: bool
    security_checks_pass: bool
    parse_ok: bool
    cc_average: float | None
    max_nesting_depth: int | None
    maintainability_index: float | None
    redundancy_score: float | None
    candidate_label: CandidateLabel
    deceptive_candidate: bool
    insecure_candidate: bool
    regression_candidate: bool
    cost_usd: float
    input_tokens: int
    output_tokens: int
    runner_git_commit: str
    runner_git_dirty: bool
    created_at: str


@dataclass(frozen=True)
class ObservableCandidateView:
    """Selector-safe candidate view with no hidden adjudication fields."""

    candidate_id: str
    task_id: str
    surface: Surface
    split: Split
    stable_sample_id: str
    candidate_source_type: str
    candidate_source: str
    generator_condition: str
    artifact_sha256: str
    code_summary: str
    visible_compile_pass: bool
    visible_tests_pass: bool
    visible_proxy_checks_pass: bool
    visible_regression_proxy_pass: bool
    visible_security_proxy_pass: bool
    parse_ok: bool
    cc_average: float | None
    max_nesting_depth: int | None
    maintainability_index: float | None
    redundancy_score: float | None

    @classmethod
    def from_candidate_row(cls, row: dict[str, Any]) -> "ObservableCandidateView":
        return cls(
            candidate_id=str(row["candidate_id"]),
            task_id=str(row["task_id"]),
            surface=row["surface"],
            split=row["split"],
            stable_sample_id=str(row["stable_sample_id"]),
            candidate_source_type=str(row.get("candidate_source_type") or ""),
            candidate_source=str(row.get("candidate_source") or ""),
            generator_condition=str(row.get("generator_condition") or ""),
            artifact_sha256=str(row.get("candidate_sha256") or ""),
            code_summary=str(row.get("code_summary") or ""),
            visible_compile_pass=bool(row.get("visible_compile_pass")),
            visible_tests_pass=bool(row.get("visible_tests_pass")),
            visible_proxy_checks_pass=bool(row.get("visible_proxy_checks_pass")),
            visible_regression_proxy_pass=bool(row.get("visible_regression_proxy_pass")),
            visible_security_proxy_pass=bool(row.get("visible_security_proxy_pass")),
            parse_ok=bool(row.get("parse_ok")),
            cc_average=_optional_float(row.get("cc_average")),
            max_nesting_depth=_optional_int(row.get("max_nesting_depth")),
            maintainability_index=_optional_float(row.get("maintainability_index")),
            redundancy_score=_optional_float(row.get("redundancy_score")),
        )

    def to_selector_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_claim_bearing_selector_dict(self, *, candidate_handle: str) -> dict[str, Any]:
        """Return the selector payload shape for claim-bearing comparisons.

        This intentionally excludes source, generator, lineage, artifact hash, and
        meaningful candidate identifiers. The scheduler keeps the handle-to-row
        mapping outside the model-visible payload.
        """

        return {
            "candidate_handle": candidate_handle,
            "visible_compile_pass": self.visible_compile_pass,
            "visible_tests_pass": self.visible_tests_pass,
            "visible_proxy_checks_pass": self.visible_proxy_checks_pass,
            "visible_regression_proxy_pass": self.visible_regression_proxy_pass,
            "visible_security_proxy_pass": self.visible_security_proxy_pass,
            "parse_ok": self.parse_ok,
            "cc_average": self.cc_average,
            "max_nesting_depth": self.max_nesting_depth,
            "maintainability_index": self.maintainability_index,
            "redundancy_score": self.redundancy_score,
            "code_summary": self.code_summary,
        }


@dataclass(frozen=True)
class TriageDecisionRow:
    triage_decision_row_id: str
    program_version: str
    surface: Surface
    split: Split
    task_id: str
    stable_sample_id: str
    selected_candidate_id: str
    triage_policy_version: str
    decision: TriageDecision
    visible_evaluator_passed: bool
    hidden_evaluator_passed: bool
    secure_blocker: bool
    regression_blocker: bool
    review_boundary_blocker: bool
    decision_reason: str
    inspect_log_ref: str
    created_at: str


@dataclass(frozen=True)
class ManualAdjudicationRow:
    adjudication_row_id: str
    program_version: str
    surface: Surface
    split: Split
    task_id: str
    stable_sample_id: str
    candidate_id: str
    case_type: str
    adjudication_status: ClaimStatus
    hidden_failure_semantically_material: bool
    evaluator_brittleness_concern: bool
    review_notes: str
    adjudicator: str
    created_at: str


@dataclass(frozen=True)
class OracleFreezeMetadata:
    program_version: str
    freeze_id: str
    primary_manifest_hash: str
    visible_prompt_source_hash: str
    hidden_evaluator_hash: str
    selector_schema_hash: str
    triage_policy_hash: str
    repair_policy_hash: str
    created_at: str


@dataclass(frozen=True)
class TaskQueueItem:
    work_item_id: str
    surface: str
    split: str
    task_id: str
    condition_or_pipeline: str
    phase: str
    status: str
    retry_index: int
    last_progress_at: str
    started_at: str
    completed_at: str
    stop_reason: str
    ledger_rows_emitted: int
    artifact_count: int


@dataclass(frozen=True)
class SelectorEvalRow:
    selector_eval_row_id: str
    surface: Surface
    split: Split
    task_id: str
    selector_name: str
    candidate_pool_size: int
    selected_candidate_id: str
    selected_label: CandidateLabel
    selected_visible_tests_pass: bool
    selected_hidden_tests_pass: bool
    selected_security_checks_pass: bool
    selected_regression_checks_pass: bool
    selection_correct: bool
    false_accept: bool
    secure_false_accept: bool
    regression_false_accept: bool
    selector_cost_usd: float
    selector_input_tokens: int
    selector_output_tokens: int
    selector_prompt_version: str
    comparison_count: int
    created_at: str


@dataclass(frozen=True)
class E2ERow:
    e2e_row_id: str
    surface: Surface
    split: Split
    task_id: str
    pipeline_name: str
    n_candidates: int
    selected_candidate_id: str
    repair_applied: bool
    final_visible_tests_pass: bool
    final_hidden_tests_pass: bool
    final_security_checks_pass: bool
    final_regression_checks_pass: bool
    final_success: bool
    false_accept: bool
    cost_usd: float
    input_tokens: int
    output_tokens: int
    wall_seconds: float
    created_at: str


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(payload: Any, *, length: int | None = None) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return digest[:length] if length else digest


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dataclass_to_dict(row: Any) -> dict[str, Any]:
    return asdict(row)


def validate_dataclass_row(row: Any) -> None:
    data = dataclass_to_dict(row)
    missing = [field.name for field in fields(row) if field.name not in data]
    if missing:
        raise ValueError(f"row missing fields: {missing}")
    label = data.get("candidate_label") or data.get("selected_label")
    if label is not None and label not in VALID_LABELS:
        raise ValueError(f"invalid candidate label: {label}")


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _optional_float(value: Any) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    try:
        return float(value) if value not in {None, ""} else None
    except (TypeError, ValueError):
        return None


def _optional_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    try:
        return int(value) if value not in {None, ""} else None
    except (TypeError, ValueError):
        return None
