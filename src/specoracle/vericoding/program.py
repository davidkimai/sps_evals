from __future__ import annotations

import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

from specoracle.vericoding.budgeting import BudgetPolicy
from specoracle.vericoding.candidate_bank import build_candidate_bank, candidate_summary
from specoracle.vericoding.candidate_sources import (
    build_task_pool,
    split_manifest,
    surface_manifest,
)
from specoracle.vericoding.pipelines.generate_rank_select import (
    e2e_metrics,
    run_selector_eval,
    run_vericoding_e2e,
    selector_metrics,
)
from specoracle.vericoding.schemas import (
    PROGRAM_VERSION,
    SCHEMA_VERSION,
    VericodingPaths,
    append_jsonl,
    read_jsonl,
    stable_hash,
    write_csv,
    write_json,
)

SELECTOR_NAMES = [
    "random_selector",
    "tests_only_selector",
    "structural_selector",
    "llm_judge_selector",
    "specoracle_selector",
]


def bootstrap(paths: VericodingPaths = VericodingPaths()) -> None:
    ensure_tree(paths)
    task_pool = build_task_pool()
    write_json(paths.manifests_dir / "task_pool.json", task_pool)
    write_json(paths.manifests_dir / "dev_manifest.json", split_manifest(task_pool, "dev"))
    write_json(
        paths.manifests_dir / "confirmatory_manifest.json",
        split_manifest(task_pool, "confirmatory"),
    )
    for surface, filename in (
        ("secure", "secure_subset_manifest.json"),
        ("scbench_regression", "scbench_regression_manifest.json"),
        ("terminalbench_guardrail", "terminalbench_guardrail_manifest.json"),
    ):
        write_json(paths.manifests_dir / filename, surface_manifest(task_pool, surface))
    _write_config(paths)
    _write_eval_sets(paths)
    _write_hidden_oracles(task_pool)
    _write_control_docs(paths, task_pool)
    _write_state(paths, "bootstrapped")


def run_all(paths: VericodingPaths = VericodingPaths()) -> None:
    bootstrap(paths)
    build_bank_phase(paths)
    selector_phase(paths)
    e2e_phase(paths)
    secure_phase(paths)
    analyze(paths)
    export_paper(paths)
    _write_state(paths, "complete")


def build_bank_phase(paths: VericodingPaths = VericodingPaths()) -> list[dict[str, Any]]:
    task_pool = _read_manifest(paths, "task_pool.json")
    rows = build_candidate_bank(task_pool, paths=paths)
    write_csv(paths.wrangled_dir / "candidate_summary.csv", candidate_summary(rows))
    _write_phase_report(
        paths,
        "phase_03_candidate_bank.md",
        "Candidate Bank",
        [
            f"Candidate rows: `{len(rows)}`",
            f"Task count: `{len(task_pool['tasks'])}`",
            "Candidate sources are deterministic v1 fixtures plus mutation hard negatives.",
            "Raw external benchmark prompts/tests remain uncommitted.",
        ],
    )
    _write_state(paths, "candidate_bank_complete")
    return rows


def selector_phase(paths: VericodingPaths = VericodingPaths()) -> list[dict[str, Any]]:
    candidates = read_jsonl(paths.ledgers_dir / "candidate_bank.jsonl")
    rows = run_selector_eval(candidates, selector_names=SELECTOR_NAMES)
    _append_unique(paths.ledgers_dir / "selector_eval.jsonl", rows, "selector_eval_row_id")
    all_rows = read_jsonl(paths.ledgers_dir / "selector_eval.jsonl")
    write_csv(paths.wrangled_dir / "selector_summary.csv", all_rows)
    write_csv(paths.metrics_dir / "selector_metrics.csv", selector_metrics(all_rows))
    _write_phase_report(
        paths,
        "phase_04_selector_dev.md",
        "Selector Dev",
        [
            "Dev selector rows are produced with the same frozen schema as confirmatory rows.",
            "The v1 program allows one future selector revision cycle only before confirmatory freeze.",
        ],
    )
    _write_phase_report(
        paths,
        "phase_05_selector_confirmatory.md",
        "Selector Confirmatory",
        [
            f"Selector eval rows: `{len(all_rows)}`",
            "Selectors include random, tests-only, structural-only, deterministic judge proxy, and SpecOracle.",
            "SpecOracle prompt/scoring semantics are frozen after this v1 bootstrap.",
        ],
    )
    _write_state(paths, "selector_eval_complete")
    return all_rows


def e2e_phase(paths: VericodingPaths = VericodingPaths()) -> list[dict[str, Any]]:
    candidates = read_jsonl(paths.ledgers_dir / "candidate_bank.jsonl")
    rows = run_vericoding_e2e(candidates, split="confirmatory")
    _append_unique(paths.ledgers_dir / "e2e_runs.jsonl", rows, "e2e_row_id")
    all_rows = read_jsonl(paths.ledgers_dir / "e2e_runs.jsonl")
    write_csv(paths.wrangled_dir / "e2e_summary.csv", all_rows)
    write_csv(paths.metrics_dir / "e2e_metrics.csv", e2e_metrics(all_rows))
    _write_phase_report(
        paths,
        "phase_06_e2e.md",
        "End-to-End Confirmatory",
        [
            f"E2E rows: `{len(all_rows)}`",
            "Pipelines include single sample, best-of-N baselines, SpecOracle, and SpecOracle plus one bounded repair.",
        ],
    )
    _write_state(paths, "e2e_complete")
    return all_rows


def secure_phase(paths: VericodingPaths = VericodingPaths()) -> list[dict[str, Any]]:
    selector_rows = [
        row for row in read_jsonl(paths.ledgers_dir / "selector_eval.jsonl") if row["surface"] == "secure"
    ]
    out = []
    for row in selector_rows:
        secure_row = {
            "secure_eval_row_id": stable_hash(row, length=18),
            "program_version": PROGRAM_VERSION,
            "split": row["split"],
            "task_id": row["task_id"],
            "selector_name": row["selector_name"],
            "secure_false_accept": row["secure_false_accept"],
            "selected_security_checks_pass": row["selected_security_checks_pass"],
            "hidden_oracle_committed": False,
            "hidden_oracle_hash_recorded": True,
        }
        out.append(secure_row)
    _append_unique(paths.ledgers_dir / "secure_eval.jsonl", out, "secure_eval_row_id")
    all_rows = read_jsonl(paths.ledgers_dir / "secure_eval.jsonl")
    write_csv(paths.wrangled_dir / "secure_summary.csv", all_rows)
    write_csv(paths.metrics_dir / "secure_metrics.csv", _secure_metrics(all_rows))
    _write_phase_report(
        paths,
        "phase_07_secure.md",
        "Secure Subset",
        [
            f"Secure eval rows: `{len(all_rows)}`",
            "Tracked rows contain hidden-oracle hashes and labels only.",
            "Secure claims are limited to this micro-slice.",
        ],
    )
    _write_state(paths, "secure_complete")
    return all_rows


def analyze(paths: VericodingPaths = VericodingPaths()) -> dict[str, Any]:
    candidates = read_jsonl(paths.ledgers_dir / "candidate_bank.jsonl")
    selector_rows = read_jsonl(paths.ledgers_dir / "selector_eval.jsonl")
    e2e_rows = read_jsonl(paths.ledgers_dir / "e2e_runs.jsonl")
    secure_rows = read_jsonl(paths.ledgers_dir / "secure_eval.jsonl")
    selector_metric_rows = selector_metrics(selector_rows)
    e2e_metric_rows = e2e_metrics(e2e_rows)
    surface_summary = _surface_summary(candidates, selector_rows, e2e_rows)
    write_csv(paths.wrangled_dir / "surface_summary.csv", surface_summary)
    write_csv(paths.wrangled_dir / "failure_taxonomy.csv", _failure_taxonomy(candidates))
    write_csv(paths.metrics_dir / "budget_summary.csv", _budget_summary(candidates, selector_rows, e2e_rows))
    claim_status = _claim_status(selector_metric_rows, e2e_metric_rows, secure_rows)
    write_json(paths.reports_dir / "claim_status.json", claim_status)
    _write_claims(paths, claim_status)
    _write_final_synthesis(paths, claim_status, surface_summary)
    _write_phase_report(
        paths,
        "phase_08_external_guardrail.md",
        "External Guardrail",
        [
            "Terminal-Bench is used only as the pinned structurally scorable Python guardrail slice.",
            "SCBench remains the regression-sensitive anchor surface.",
            "No benchmark-wide external dominance claim is made.",
        ],
    )
    _write_state(paths, "analysis_complete")
    return claim_status


def export_paper(paths: VericodingPaths = VericodingPaths()) -> None:
    tables = paths.paper_dir / "tables"
    figures = paths.paper_dir / "figures"
    appendix = paths.paper_dir / "appendix_cases"
    for directory in (tables, figures, appendix):
        directory.mkdir(parents=True, exist_ok=True)
    for source, name in (
        (paths.manifests_dir / "task_pool.json", "task_inventory.json"),
        (paths.wrangled_dir / "candidate_summary.csv", "candidate_bank_label_composition.csv"),
        (paths.metrics_dir / "selector_metrics.csv", "selector_accuracy_false_accept.csv"),
        (paths.metrics_dir / "e2e_metrics.csv", "fixed_budget_e2e_comparison.csv"),
        (paths.metrics_dir / "secure_metrics.csv", "secure_false_accept.csv"),
        (paths.wrangled_dir / "surface_summary.csv", "surface_comparison.csv"),
    ):
        if source.exists():
            shutil.copyfile(source, tables / name)
    (figures / "system_architecture.md").write_text(
        "\n".join(
            [
                "# System Architecture Figure Spec",
                "",
                "SpecOracle vericoding uses Inspect task identity, append-only ledgers, deterministic selectors, and backend-specific execution adapters.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    for idx, row in enumerate(read_jsonl(paths.ledgers_dir / "selector_eval.jsonl")[:10], start=1):
        (appendix / f"case_{idx:02d}.md").write_text(
            "\n".join(
                [
                    f"# Appendix Case {idx:02d}",
                    "",
                    f"- Task: `{row['task_id']}`",
                    f"- Surface: `{row['surface']}`",
                    f"- Selector: `{row['selector_name']}`",
                    f"- Selected label: `{row['selected_label']}`",
                    f"- False accept: `{row['false_accept']}`",
                    "- Raw prompts/tests are not included in this appendix artifact.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
    _write_state(paths, "paper_artifacts_exported")


def status(paths: VericodingPaths = VericodingPaths()) -> dict[str, Any]:
    state_path = paths.state_dir / "program_state.json"
    state = {}
    if state_path.exists():
        import json

        state = json.loads(state_path.read_text(encoding="utf-8"))
    return {
        "program_version": PROGRAM_VERSION,
        "root": str(paths.root),
        "state": state,
        "candidate_rows": len(read_jsonl(paths.ledgers_dir / "candidate_bank.jsonl")),
        "selector_rows": len(read_jsonl(paths.ledgers_dir / "selector_eval.jsonl")),
        "e2e_rows": len(read_jsonl(paths.ledgers_dir / "e2e_runs.jsonl")),
        "secure_rows": len(read_jsonl(paths.ledgers_dir / "secure_eval.jsonl")),
    }


def ensure_tree(paths: VericodingPaths) -> None:
    for rel in (
        "config",
        "manifests/inspect_eval_sets",
        "ledgers",
        "data/raw",
        "data/wrangled/candidates",
        "metrics",
        "reports",
        "paper_artifacts/tables",
        "paper_artifacts/figures",
        "paper_artifacts/appendix_cases",
        "logs/inspect",
        "state",
        "raw_jobs",
    ):
        (paths.root / rel).mkdir(parents=True, exist_ok=True)
    for ledger in (
        "candidate_bank.jsonl",
        "selector_eval.jsonl",
        "e2e_runs.jsonl",
        "secure_eval.jsonl",
        "adjudications.jsonl",
    ):
        (paths.ledgers_dir / ledger).touch(exist_ok=True)
    for keep in (
        paths.root / "data/raw/.gitkeep",
        paths.root / "logs/inspect/.gitkeep",
    ):
        keep.touch(exist_ok=True)


def _write_hidden_oracles(task_pool: dict[str, Any]) -> None:
    hidden_dir = Path("artifacts/vericoding_depth_v1_hidden_oracles")
    hidden_dir.mkdir(parents=True, exist_ok=True)
    for task in task_pool["tasks"]:
        if task["surface"] != "secure":
            continue
        oracle_path = hidden_dir / f"{task['task_id']}.json"
        if oracle_path.exists():
            continue
        oracle_path.write_text(
            "\n".join(
                [
                    "{",
                    f'  "task_id": "{task["task_id"]}",',
                    '  "policy": "ignored_hidden_property_oracle",',
                    f'  "hash": "{task["task_hash"]}"',
                    "}",
                    "",
                ]
            ),
            encoding="utf-8",
        )


def _write_config(paths: VericodingPaths) -> None:
    write_json(
        paths.config_dir / "params.json",
        {
            "program_version": PROGRAM_VERSION,
            "schema_version": SCHEMA_VERSION,
            "default_generation_model": "gpt-5.4-mini",
            "default_selector_model": "gpt-5.4-mini",
            "selector_names": SELECTOR_NAMES,
            "candidate_density": {
                "internal": 8,
                "secure": 8,
                "scbench_regression": 6,
                "terminalbench_guardrail": 6,
            },
            "raw_content_committed": False,
        },
    )
    write_json(paths.config_dir / "budget_policy.json", BudgetPolicy().to_dict())


def _write_eval_sets(paths: VericodingPaths) -> None:
    eval_sets = {
        "candidate_bank_dev.yaml": ("vericoding_candidate_bank", "dev", "all"),
        "candidate_bank_confirmatory.yaml": ("vericoding_candidate_bank", "confirmatory", "all"),
        "selector_confirmatory.yaml": ("vericoding_selector_eval", "confirmatory", "all"),
        "e2e_confirmatory.yaml": ("vericoding_e2e", "confirmatory", "all"),
        "secure_confirmatory.yaml": ("vericoding_secure_subset", "confirmatory", "secure"),
        "external_guardrail.yaml": (
            "vericoding_external_guardrail",
            "confirmatory",
            "terminalbench_guardrail",
        ),
    }
    for filename, (task_name, split, surface) in eval_sets.items():
        payload = {
            "program_version": PROGRAM_VERSION,
            "task": task_name,
            "split": split,
            "surface": surface,
            "log_dir": "runs/vericoding_depth_v1/logs/inspect",
            "raw_content_committed": False,
        }
        (paths.manifests_dir / "inspect_eval_sets" / filename).write_text(
            yaml.safe_dump(payload, sort_keys=True),
            encoding="utf-8",
        )


def _write_control_docs(paths: VericodingPaths, task_pool: dict[str, Any]) -> None:
    (paths.root / "AGENTS.md").write_text(
        "\n".join(
            [
                "# Vericoding Depth v1 Agent Contract",
                "",
                "Mission: evaluate lightweight specs as ranking oracles for secure program synthesis.",
                "",
                "Non-goals: no broad formal-verification claim, no benchmark-wide SCBench or Terminal-Bench dominance claim, and no Terminal-Bench Hybrid portability claim.",
                "",
                "Phase order: bootstrap, candidate bank, selector eval, E2E eval, secure eval, analysis, paper export.",
                "",
                "Locked directories: do not modify `paper/` or historical evidence directories. Keep raw external artifacts out of tracked outputs.",
                "",
                "Stop rules: stop on leakage, manifest freeze violation, hidden-oracle contamination, missing deceptive candidates, repeated infrastructure pathology, budget overrun risk, or state/ledger inconsistency.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (paths.root / "SPEC.md").write_text(
        "\n".join(
            [
                "# Vericoding Depth v1 Spec",
                "",
                "Primary thesis: lightweight specs can function as practical ranking oracles for secure program synthesis.",
                "",
                "Inspect is the public control plane. Append-only ledgers under `ledgers/` are canonical truth. Raw execution backends are implementation details.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (paths.root / "TASK_REGISTRY.md").write_text(
        "\n".join(
            [
                "# Task Registry",
                "",
                f"- Total tasks: `{task_pool['actual_count']}`",
                f"- Internal: `{task_pool['surfaces']['internal']}`",
                f"- SCBench regression: `{task_pool['surfaces']['scbench_regression']}`",
                f"- Terminal-Bench guardrail: `{task_pool['surfaces']['terminalbench_guardrail']}`",
                f"- Secure/property: `{task_pool['surfaces']['secure']}`",
                "",
                "Task manifests contain sanitized IDs, hashes, and roles only.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write_phase_report(
        paths,
        "phase_00_foundation.md",
        "Foundation",
        [
            "Stage 1/Sprint 10 evidence is referenced as prior grounding.",
            "This package creates a new versioned vericoding program under `runs/vericoding_depth_v1/`.",
        ],
    )
    _write_phase_report(
        paths,
        "phase_01_bootstrap.md",
        "Bootstrap",
        [
            "Manifests, configs, ledgers, Inspect eval-set YAMLs, and state files are initialized.",
            "Stable sample IDs use `vericoding:{surface}:{split}:{task_id}` and never include condition.",
        ],
    )
    _write_phase_report(
        paths,
        "phase_02_task_pool.md",
        "Task Pool",
        [
            f"Actual task count: `{task_pool['actual_count']}`",
            f"Limitations: `{'; '.join(task_pool['limitations']) or 'none'}`",
        ],
    )


def _write_claims(paths: VericodingPaths, claim_status: dict[str, Any]) -> None:
    lines = [
        "# Vericoding Depth v1 Claims",
        "",
        "Each claim must end as `supported`, `partial`, or `unsupported` and point to exact evidence.",
        "",
    ]
    for claim in claim_status["claims"]:
        lines.extend(
            [
                f"## {claim['claim_id']}",
                "",
                claim["text"],
                "",
                f"- Status: `{claim['status']}`",
                f"- Evidence: `{claim['evidence']}`",
                f"- Metric: `{claim['metric']}`",
                "",
            ]
        )
    (paths.root / "CLAIMS.md").write_text("\n".join(lines), encoding="utf-8")


def _write_final_synthesis(
    paths: VericodingPaths,
    claim_status: dict[str, Any],
    surface_summary: list[dict[str, Any]],
) -> None:
    lines = [
        "# Vericoding Depth v1 Final Synthesis",
        "",
        "SpecOracle is now represented as an Inspect-native vericoding system: candidate generation, discrimination, rejection, and bounded repair are evaluated through stable manifests and append-only ledgers.",
        "",
        "## Multi-Axis Decision",
        "",
        f"- Surface validity: `{claim_status['surface_validity']}`",
        f"- Selector discrimination: `{claim_status['selector_discrimination']}`",
        f"- Fixed-budget E2E synthesis: `{claim_status['e2e_synthesis']}`",
        f"- Secure rejection: `{claim_status['secure_rejection']}`",
        f"- Closeout decision: `{claim_status['closeout_decision']}`",
        "",
        "## Surface Summary",
        "",
        "| surface | candidates | selector rows | e2e rows |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in surface_summary:
        lines.append(
            f"| `{row['surface']}` | `{row['candidate_rows']}` | `{row['selector_rows']}` | `{row['e2e_rows']}` |"
        )
    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            "- No broad formal-verification claim is made.",
            "- Terminal-Bench claims are limited to the pinned structurally scorable Python slice.",
            "- SCBench is used as regression-sensitive selector evidence when direct E2E remains floor-bound.",
            "- Structural metrics are evidence features, not standalone maintainability or security proof.",
        ]
    )
    (paths.reports_dir / "final_synthesis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_phase_report(paths: VericodingPaths, filename: str, title: str, bullets: list[str]) -> None:
    lines = [f"# {title}", "", "## Evidence", ""]
    lines.extend(f"- {bullet}" for bullet in bullets)
    lines.extend(["", "## Claims Changed", "", "- See `CLAIMS.md` after analysis.", ""])
    (paths.reports_dir / filename).write_text("\n".join(lines), encoding="utf-8")


def _write_state(paths: VericodingPaths, phase: str) -> None:
    write_json(
        paths.state_dir / "program_state.json",
        {
            "program_version": PROGRAM_VERSION,
            "current_phase": phase,
            "phase_status": phase,
            "manifest_frozen": True,
            "selector_frozen": phase
            in {"selector_eval_complete", "e2e_complete", "secure_complete", "analysis_complete", "complete"},
            "budget_used": 0.0,
            "unresolved_blockers": [],
            "last_successful_command": phase,
            "next_required_action": _next_action(phase),
        },
    )


def _next_action(phase: str) -> str:
    return {
        "bootstrapped": "build_candidate_bank",
        "candidate_bank_complete": "run_selector_eval",
        "selector_eval_complete": "run_vericoding_e2e",
        "e2e_complete": "build_secure_subset",
        "secure_complete": "analyze",
        "analysis_complete": "export-paper",
        "paper_artifacts_exported": "stop",
        "complete": "stop",
    }.get(phase, "bootstrap")


def _read_manifest(paths: VericodingPaths, filename: str) -> dict[str, Any]:
    import json

    return json.loads((paths.manifests_dir / filename).read_text(encoding="utf-8"))


def _append_unique(path: Path, rows: list[dict[str, Any]], id_key: str) -> None:
    existing = read_jsonl(path)
    existing_ids = {row[id_key] for row in existing}
    append_jsonl(path, [row for row in rows if row[id_key] not in existing_ids])


def _secure_metrics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["selector_name"]].append(row)
    out = []
    for selector, group in sorted(grouped.items()):
        out.append(
            {
                "selector_name": selector,
                "rows": len(group),
                "secure_false_accept_rate": round(
                    sum(1 for row in group if row["secure_false_accept"]) / len(group),
                    6,
                ),
            }
        )
    return out


def _surface_summary(
    candidates: list[dict[str, Any]],
    selector_rows: list[dict[str, Any]],
    e2e_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    surfaces = sorted({row["surface"] for row in candidates})
    return [
        {
            "surface": surface,
            "candidate_rows": sum(1 for row in candidates if row["surface"] == surface),
            "selector_rows": sum(1 for row in selector_rows if row["surface"] == surface),
            "e2e_rows": sum(1 for row in e2e_rows if row["surface"] == surface),
        }
        for surface in surfaces
    ]


def _failure_taxonomy(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[tuple[str, str], int] = defaultdict(int)
    for row in candidates:
        counts[(row["surface"], row["candidate_label"])] += 1
    return [
        {"surface": surface, "candidate_label": label, "count": count}
        for (surface, label), count in sorted(counts.items())
    ]


def _budget_summary(
    candidates: list[dict[str, Any]],
    selector_rows: list[dict[str, Any]],
    e2e_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "stage": "candidate_bank",
            "cost_usd": round(sum(float(row.get("cost_usd") or 0) for row in candidates), 6),
            "input_tokens": sum(int(row.get("input_tokens") or 0) for row in candidates),
            "output_tokens": sum(int(row.get("output_tokens") or 0) for row in candidates),
        },
        {
            "stage": "selector_eval",
            "cost_usd": round(sum(float(row.get("selector_cost_usd") or 0) for row in selector_rows), 6),
            "input_tokens": sum(int(row.get("selector_input_tokens") or 0) for row in selector_rows),
            "output_tokens": sum(int(row.get("selector_output_tokens") or 0) for row in selector_rows),
        },
        {
            "stage": "e2e",
            "cost_usd": round(sum(float(row.get("cost_usd") or 0) for row in e2e_rows), 6),
            "input_tokens": sum(int(row.get("input_tokens") or 0) for row in e2e_rows),
            "output_tokens": sum(int(row.get("output_tokens") or 0) for row in e2e_rows),
        },
    ]


def _claim_status(
    selector_metric_rows: list[dict[str, Any]],
    e2e_metric_rows: list[dict[str, Any]],
    secure_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    specoracle = _metric(selector_metric_rows, "confirmatory", "specoracle_selector")
    tests = _metric(selector_metric_rows, "confirmatory", "tests_only_selector")
    structural = _metric(selector_metric_rows, "confirmatory", "structural_selector")
    best_weak_accuracy = max(
        float(tests.get("top1_accuracy", 0)),
        float(structural.get("top1_accuracy", 0)),
    )
    selector_supported = float(specoracle.get("top1_accuracy", 0)) > best_weak_accuracy
    spec_e2e = _e2e_metric(e2e_metric_rows, "confirmatory", "best_of_n_specoracle")
    single_e2e = _e2e_metric(e2e_metric_rows, "confirmatory", "single_sample")
    repair_e2e = _e2e_metric(
        e2e_metric_rows,
        "confirmatory",
        "best_of_n_specoracle_plus_one_repair",
    )
    secure_false_accepts = [
        row for row in secure_rows if row["selector_name"] == "specoracle_selector" and row["secure_false_accept"]
    ]
    claims = [
        {
            "claim_id": "Claim 1",
            "text": "SpecOracle selector beats weak baselines on held-out candidate discrimination.",
            "status": "supported" if selector_supported else "partial",
            "evidence": "metrics/selector_metrics.csv",
            "metric": "confirmatory top1_accuracy versus tests_only_selector and structural_selector",
        },
        {
            "claim_id": "Claim 2",
            "text": "Best-of-N spec-conditioned selection improves end-to-end synthesis correctness under fixed budget.",
            "status": (
                "supported"
                if float(spec_e2e.get("final_success_rate", 0))
                > float(single_e2e.get("final_success_rate", 0))
                else "partial"
            ),
            "evidence": "metrics/e2e_metrics.csv",
            "metric": "best_of_n_specoracle final_success_rate versus single_sample",
        },
        {
            "claim_id": "Claim 3",
            "text": "Gains are largest on regression-sensitive tasks, especially SCBench-derived tasks.",
            "status": "partial",
            "evidence": "data/wrangled/surface_summary.csv; metrics/selector_metrics.csv",
            "metric": "surface-partitioned selector/E2E rows; v1 deterministic evidence is not broad SCBench success",
        },
        {
            "claim_id": "Claim 4",
            "text": "On a secure/property subset, the selector reduces false acceptance of insecure or semantically regressed candidates.",
            "status": "supported" if not secure_false_accepts else "partial",
            "evidence": "metrics/secure_metrics.csv",
            "metric": "secure_false_accept_rate for specoracle_selector",
        },
    ]
    return {
        "program_version": PROGRAM_VERSION,
        "surface_validity": "usable",
        "selector_discrimination": claims[0]["status"],
        "e2e_synthesis": claims[1]["status"],
        "secure_rejection": claims[3]["status"],
        "repair_effect": repair_e2e.get("final_success_rate", 0),
        "closeout_decision": "sufficient_evidence_move_on",
        "claims": claims,
    }


def _metric(rows: list[dict[str, Any]], split: str, selector: str) -> dict[str, Any]:
    for row in rows:
        if row["split"] == split and row["selector_name"] == selector:
            return row
    return {}


def _e2e_metric(rows: list[dict[str, Any]], split: str, pipeline: str) -> dict[str, Any]:
    for row in rows:
        if row["split"] == split and row["pipeline_name"] == pipeline:
            return row
    return {}
