from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any, Iterable

import yaml

from specoracle.config import (
    GenerationMode,
    ModelSettings,
    Provider,
    Task,
    default_model_settings,
    oracle_spec_for_task,
    oracle_spec_label_for_task,
    variant_name,
)
from specoracle.evaluator import (
    DEFAULT_PYTEST_DOCKER_IMAGE,
    EvaluationResult,
    JudgeResult,
    PytestResult,
    StaticMetrics,
    benchmark_pytest_sandbox,
    evaluate_code,
    prepare_pytest_sandbox,
    smoke_test_dafny_sandbox,
)
from specoracle.generator import (
    GenerationResult,
    SpecOracleGenerator,
    build_llm_client,
    generation_result_from_mapping,
)
from specoracle.hybrid import HybridConstraints, HybridOracle
from specoracle.stress import ChainStepResult, SpecArena, StressResult, stress_result_from_mapping


_SLOPBENCH_MIN_TASK_IDS = frozenset(
    {
        "nested_json_index",
        "retry_state_machine",
        "event_window_summary",
        "dependency_order",
        "policy_merge",
        "legacy_invoice_spec",
        "thread_safe_counter",
        "config_precedence_merge",
        "cli_argument_validation",
        "csv_sales_aggregate",
        "retry_backoff_schedule",
        "json_path_projection",
        "sliding_window_limiter",
        "archival_binding_spec",
        "dedupe_event_stream",
        "round_robin_scheduler",
        "incident_desk_spec",
        "log_sessionizer",
        "feature_flag_matrix",
        "inventory_reorder",
    }
)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate":
        tasks = load_tasks(Path(args.dataset), limit=args.limit)
        tasks = _apply_oracle_skill(tasks, getattr(args, "oracle_skill", None))
        settings = _settings_from_args(args, role="generator")
        client = build_llm_client(settings)
        generator = SpecOracleGenerator(client, settings)
        results = generate_tasks(
            generator,
            tasks,
            Path(args.out),
            modes=tuple(args.modes),
            samples=args.samples,
            hybrid_constraints=_hybrid_constraints_from_args(args),
            pytest_timeout_seconds=getattr(args, "pytest_timeout", 10.0),
        )
        print(f"generated {len(results)} artifact(s) into {Path(args.out).resolve()}")
        return 0

    if args.command == "evaluate":
        tasks = {task.id: task for task in load_tasks(Path(args.dataset), limit=args.limit)}
        judge_settings, judge_client = _judge_from_args(args)
        results = evaluate_artifacts(
            tasks=tasks,
            out_dir=Path(args.out),
            pytest_timeout_seconds=args.pytest_timeout,
            judge_settings=judge_settings,
            judge_client=judge_client,
        )
        results.extend(
            evaluate_human_references(
                tasks=tasks.values(),
                out_dir=Path(args.out),
                pytest_timeout_seconds=args.pytest_timeout,
                judge_settings=judge_settings,
                judge_client=judge_client,
                skip_keys={
                    _summary_key(
                        task_id=result.task_id,
                        variant=result.variant,
                        provider=result.provider,
                        model=result.model,
                        sample_index=result.sample_index,
                    )
                    for result in results
                },
            )
        )
        write_summary(results, Path(args.out) / "summary.csv")
        print(f"evaluated {len(results)} artifact(s); summary at {(Path(args.out) / 'summary.csv').resolve()}")
        return 0

    if args.command == "run":
        tasks = load_tasks(Path(args.dataset), limit=args.limit)
        tasks = _apply_oracle_skill(tasks, getattr(args, "oracle_skill", None))
        settings = _settings_from_args(args, role="generator")
        client = build_llm_client(settings)
        generator = SpecOracleGenerator(client, settings)
        generated = generate_tasks(
            generator,
            tasks,
            Path(args.out),
            modes=tuple(args.modes),
            samples=args.samples,
            hybrid_constraints=_hybrid_constraints_from_args(args),
            pytest_timeout_seconds=args.pytest_timeout,
        )

        judge_settings, judge_client = _judge_from_args(args)
        task_map = {task.id: task for task in tasks}
        results = evaluate_generation_results(
            generated=generated,
            task_map=task_map,
            out_dir=Path(args.out),
            pytest_timeout_seconds=args.pytest_timeout,
            judge_settings=judge_settings,
            judge_client=judge_client,
        )
        results.extend(
            evaluate_human_references(
                tasks=tasks,
                out_dir=Path(args.out),
                pytest_timeout_seconds=args.pytest_timeout,
                judge_settings=judge_settings,
                judge_client=judge_client,
            )
        )
        write_summary(results, Path(args.out) / "summary.csv")
        print(
            f"generated and evaluated {len(results)} artifact(s); "
            f"summary at {(Path(args.out) / 'summary.csv').resolve()}"
        )
        return 0

    if args.command == "stress":
        run_dir = Path(args.run_dir)
        task_map = (
            {task.id: task for task in load_tasks(Path(args.dataset), limit=args.limit)}
            if args.dataset
            else None
        )
        settings = _settings_from_args(args, role="maintenance")
        arena = SpecArena(
            client=build_llm_client(settings),
            settings=settings,
            pytest_timeout_seconds=args.pytest_timeout,
        )
        stress_results = arena.stress_run_dir(
            run_dir=run_dir,
            task_map=task_map,
            context_ablation=args.context_ablation,
        )
        chain_results = arena.chain_run_dir(
            run_dir=run_dir,
            task_map=task_map,
            chain_depth=args.chain_depth,
        )
        if chain_results:
            write_chain_summary(chain_results, run_dir)
        evaluations = load_evaluation_results(run_dir)
        write_summary(evaluations, run_dir / "summary.csv", stress_results=stress_results)
        print(
            f"stressed {len(stress_results)} artifact(s); "
            f"summary at {(run_dir / 'summary.csv').resolve()}"
        )
        return 0

    if args.command == "validate":
        tasks = load_tasks(Path(args.dataset), limit=args.limit)
        if args.run_dir:
            errors = validate_run_dir(
                run_dir=Path(args.run_dir),
                tasks=tasks,
                samples=args.samples,
                context_ablation=args.context_ablation,
            )
            success_target = str(Path(args.run_dir).resolve())
        else:
            errors = validate_dataset(Path(args.dataset), tasks=tasks)
            success_target = str(Path(args.dataset).resolve())
        if errors:
            for error in errors:
                print(f"validation error: {error}")
            return 1
        print(f"validated {success_target}")
        return 0

    if args.command == "sandbox":
        image = args.image or DEFAULT_PYTEST_DOCKER_IMAGE
        if args.sandbox_command == "prepare":
            prepare_pytest_sandbox(image=image)
            print(f"prepared Docker pytest sandbox image {image}")
            return 0
        if args.sandbox_command == "benchmark":
            metrics = benchmark_pytest_sandbox(
                iterations=args.iterations,
                timeout_seconds=args.pytest_timeout,
                image=image,
            )
            print(json.dumps(metrics, indent=2, sort_keys=True))
            return 0
        if args.sandbox_command == "dafny-smoke":
            metrics = smoke_test_dafny_sandbox(
                timeout_seconds=args.pytest_timeout,
                image=image,
            )
            print(json.dumps(metrics, indent=2, sort_keys=True))
            return 0
        parser.error(f"unknown sandbox command: {args.sandbox_command}")
        return 2

    parser.error(f"unknown command: {args.command}")
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="specoracle",
        description="Run baseline vs Zen-oracle secure program synthesis evaluations.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="generate code artifacts")
    _add_generation_args(generate)
    _add_dataset_args(generate)

    evaluate = subparsers.add_parser("evaluate", help="evaluate generated code artifacts")
    _add_dataset_args(evaluate)
    _add_evaluation_args(evaluate)

    run = subparsers.add_parser("run", help="generate and evaluate in one pass")
    _add_generation_args(run)
    _add_dataset_args(run)
    _add_evaluation_args(run)

    stress = subparsers.add_parser("stress", help="run Day 2 SpecArena maintenance stress tests")
    stress.add_argument("--run-dir", required=True, help="directory containing generation artifacts")
    stress.add_argument("--dataset", default=None, help="optional task dataset for older artifacts")
    stress.add_argument("--limit", type=int, default=None, help="optional task limit")
    stress.add_argument("--provider", choices=("openai", "anthropic", "google", "mock"), default="openai")
    stress.add_argument("--model", default=None)
    stress.add_argument("--temperature", type=float, default=None)
    stress.add_argument("--require-temperature", action="store_true")
    stress.add_argument("--max-tokens", type=int, default=None)
    stress.add_argument("--llm-timeout", type=float, default=None)
    stress.add_argument("--pytest-timeout", type=float, default=10.0)
    stress.add_argument("--context-ablation", action="store_true")
    stress.add_argument("--chain-depth", type=int, default=1)

    validate = subparsers.add_parser("validate", help="validate a task dataset or completed run directory")
    validate.add_argument("--run-dir", default=None)
    validate.add_argument("--dataset", required=True)
    validate.add_argument("--limit", type=int, default=None)
    validate.add_argument("--samples", type=int, default=1)
    validate.add_argument("--context-ablation", action="store_true")

    sandbox = subparsers.add_parser("sandbox", help="manage the Docker pytest sandbox")
    sandbox_subparsers = sandbox.add_subparsers(dest="sandbox_command", required=True)
    prepare = sandbox_subparsers.add_parser("prepare", help="build the prepared pytest image")
    prepare.add_argument("--image", default=DEFAULT_PYTEST_DOCKER_IMAGE)

    benchmark = sandbox_subparsers.add_parser("benchmark", help="time repeated warm pytest runs")
    benchmark.add_argument("--image", default=DEFAULT_PYTEST_DOCKER_IMAGE)
    benchmark.add_argument("--iterations", type=int, default=5)
    benchmark.add_argument("--pytest-timeout", type=float, default=10.0)

    dafny_smoke = sandbox_subparsers.add_parser(
        "dafny-smoke",
        help="verify, compile, import, and pytest a tiny Dafny artifact",
    )
    dafny_smoke.add_argument("--image", default=DEFAULT_PYTEST_DOCKER_IMAGE)
    dafny_smoke.add_argument("--pytest-timeout", type=float, default=30.0)

    return parser


def _add_dataset_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dataset", required=True, help="directory or file containing task YAML/JSON")
    parser.add_argument("--out", required=True, help="output run directory")
    parser.add_argument("--limit", type=int, default=None, help="optional task limit for smoke runs")


def _add_generation_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--provider", choices=("openai", "anthropic", "google", "mock"), default="openai")
    parser.add_argument("--model", default=None)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--llm-timeout", type=float, default=None)
    parser.add_argument(
        "--modes",
        nargs="+",
        choices=(
            "baseline",
            "oracle",
            "oracle_karpathy",
            "oracle_dafny",
            "neutral_style",
            "hybrid",
            "modular_discovery",
        ),
        default=["baseline", "oracle"],
        help="generation modes to run",
    )
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--require-temperature", action="store_true")
    parser.add_argument("--max-cc", type=int, default=None)
    parser.add_argument("--max-nesting", type=int, default=None)
    parser.add_argument("--hybrid-max-retries", type=int, default=3)
    parser.add_argument("--hybrid-require-pytest", dest="hybrid_require_pytest", action="store_true", default=True)
    parser.add_argument("--no-hybrid-require-pytest", dest="hybrid_require_pytest", action="store_false")
    parser.add_argument(
        "--oracle-skill",
        type=str,
        default=None,
        help=(
            "Path to an Agent Skills SKILL.md to use as the oracle. "
            "See https://developers.openai.com/codex/skills"
        ),
    )


def _add_evaluation_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--pytest-timeout", type=float, default=10.0)
    parser.add_argument("--judge-provider", choices=("none", "openai", "anthropic", "google", "mock"), default="none")
    parser.add_argument("--judge-model", default=None)
    parser.add_argument("--judge-temperature", type=float, default=None)
    parser.add_argument("--judge-max-tokens", type=int, default=None)
    parser.add_argument("--judge-timeout", type=float, default=None)


def load_tasks(path: Path, *, limit: int | None = None) -> list[Task]:
    if not path.exists():
        raise FileNotFoundError(path)

    payloads: list[dict[str, Any]] = []
    if path.is_file():
        payloads.extend(_load_task_file(path))
    else:
        for child in sorted(path.iterdir()):
            if child.suffix.lower() in {".json", ".jsonl", ".yaml", ".yml"}:
                payloads.extend(_load_task_file(child))

    tasks = [Task.from_mapping(payload) for payload in payloads]
    return tasks[:limit] if limit is not None else tasks


def _apply_oracle_skill(tasks: list[Task], oracle_skill: str | None) -> list[Task]:
    if not oracle_skill:
        return tasks

    from specoracle.skills import load_skill_oracle

    skill_name, skill_body = load_skill_oracle(oracle_skill)
    print(f"Loaded oracle skill: {skill_name}")
    return [
        Task.from_mapping({**task.to_mapping(), "custom_spec_override": skill_body})
        for task in tasks
    ]


def _load_task_file(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))

    if isinstance(payload, list):
        return [dict(item) for item in payload]
    return [dict(payload)]


def generate_tasks(
    generator: SpecOracleGenerator,
    tasks: Iterable[Task],
    out_dir: Path,
    *,
    modes: tuple[str, ...],
    samples: int = 1,
    hybrid_constraints: HybridConstraints | None = None,
    pytest_timeout_seconds: float = 10.0,
) -> list[GenerationResult]:
    if samples <= 0:
        raise ValueError("--samples must be positive")
    out_dir.mkdir(parents=True, exist_ok=True)
    results: list[GenerationResult] = []
    for task in tasks:
        for raw_mode in modes:
            mode = _as_generation_mode(raw_mode)
            for sample_index in range(samples):
                existing = load_existing_generation_result(
                    out_dir=out_dir,
                    task=task,
                    mode=mode,
                    provider=generator.settings.provider,
                    model=generator.settings.model,
                    sample_index=sample_index,
                    requested_temperature=generator.settings.temperature,
                    require_temperature=generator.settings.require_temperature,
                )
                if existing is not None:
                    results.append(existing)
                    continue
                if mode == "hybrid":
                    hybrid = HybridOracle(
                        client=generator.client,
                        settings=generator.settings,
                        constraints=hybrid_constraints or HybridConstraints(),
                        pytest_timeout_seconds=pytest_timeout_seconds,
                    )
                    result = hybrid.generate_with_gates(task=task, sample_index=sample_index)
                else:
                    result = generator.generate(task, mode=mode, sample_index=sample_index)
                write_generation_result(result, out_dir)
                results.append(result)
    return results


def load_existing_generation_result(
    *,
    out_dir: Path,
    task: Task,
    mode: GenerationMode,
    provider: str,
    model: str,
    sample_index: int,
    requested_temperature: float,
    require_temperature: bool,
) -> GenerationResult | None:
    variant = variant_name(mode)
    artifact_dir = _artifact_dir(
        out_dir=out_dir,
        task_id=task.id,
        variant=variant,
        provider=provider,
        model=model,
        sample_index=sample_index,
    )
    generation_path = artifact_dir / "generation.json"
    generation_exists = generation_path.exists()
    if not generation_exists:
        if (artifact_dir / "solution.py").exists() or (artifact_dir / "solution.dfy").exists():
            raise RuntimeError(
                "partial generation artifact for "
                f"{task.id}/{variant}/{provider}/{model}/s{sample_index}: "
                "expected generation.json beside source artifact"
            )
        return None

    try:
        payload = json.loads(generation_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"malformed generation artifact: {generation_path}") from exc

    artifact_language = str(payload.get("artifact_language") or "python")
    solution_path = _source_path_for_artifact(artifact_dir, artifact_language)
    if not solution_path.exists():
        raise RuntimeError(
            "partial generation artifact for "
            f"{task.id}/{variant}/{provider}/{model}/s{sample_index}: "
            f"expected both generation.json and {solution_path.name}"
        )

    expected_key = _summary_key(
        task_id=task.id,
        variant=variant,
        provider=provider,
        model=model,
        sample_index=sample_index,
    )
    if _payload_key(payload) != expected_key:
        raise RuntimeError(
            "generation artifact key mismatch for "
            f"{generation_path}: expected {expected_key}, found {_payload_key(payload)}"
        )
    if str(payload.get("mode")) != mode:
        raise RuntimeError(
            f"generation artifact mode mismatch for {generation_path}: "
            f"expected {mode}, found {payload.get('mode')}"
        )
    actual_requested_temperature = _optional_float(payload.get("requested_temperature"))
    if actual_requested_temperature != requested_temperature:
        raise RuntimeError(
            f"generation artifact temperature mismatch for {generation_path}: "
            f"expected requested_temperature={requested_temperature}, "
            f"found {actual_requested_temperature}"
        )
    if require_temperature and _optional_float(payload.get("effective_temperature")) is None:
        raise RuntimeError(
            f"generation artifact missing effective_temperature for required-temperature run: "
            f"{generation_path}"
        )

    solution_code = solution_path.read_text(encoding="utf-8").rstrip("\n")
    payload_code = str(payload.get("code") or "").rstrip("\n")
    if payload_code != solution_code:
        raise RuntimeError(
            f"generation artifact code mismatch between {generation_path} and {solution_path}"
        )
    return generation_result_from_mapping(payload, code=solution_code)


def write_generation_result(result: GenerationResult, out_dir: Path) -> Path:
    artifact_dir = _artifact_dir(
        out_dir=out_dir,
        task_id=result.task_id,
        variant=result.variant,
        provider=result.provider,
        model=result.model,
        sample_index=result.sample_index,
    )
    artifact_dir.mkdir(parents=True, exist_ok=True)
    _source_path_for_artifact(artifact_dir, result.artifact_language).write_text(
        result.code + "\n",
        encoding="utf-8",
    )
    (artifact_dir / "generation.json").write_text(
        json.dumps(result.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return artifact_dir


def write_human_reference_artifact(task: Task, out_dir: Path) -> Path:
    artifact_dir = _artifact_dir(
        out_dir=out_dir,
        task_id=task.id,
        variant="human_reference",
        provider="human",
        model="expert",
        sample_index=0,
    )
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "solution.py").write_text(task.human_reference.rstrip() + "\n", encoding="utf-8")
    payload = {
        "task_id": task.id,
        "mode": "human_reference",
        "variant": "human_reference",
        "provider": "human",
        "model": "expert",
        "sample_index": 0,
        "requested_temperature": None,
        "effective_temperature": None,
        "entry_point": task.entry_point,
        "task": task.to_mapping(),
        "oracle_spec": oracle_spec_for_task(task),
        "oracle_spec_label": oracle_spec_label_for_task(task),
        "code": task.human_reference,
        "raw_response": task.human_reference,
        "system_prompt": "",
        "user_prompt": "",
        "artifact_language": "python",
        "metadata": None,
    }
    (artifact_dir / "generation.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return artifact_dir


def evaluate_artifacts(
    *,
    tasks: dict[str, Task],
    out_dir: Path,
    pytest_timeout_seconds: float,
    judge_settings: ModelSettings | None,
    judge_client: Any,
) -> list[EvaluationResult]:
    results: list[EvaluationResult] = []
    for generation_path in sorted(out_dir.rglob("generation.json")):
        payload = json.loads(generation_path.read_text(encoding="utf-8"))
        task = tasks[payload["task_id"]]
        artifact_language = str(payload.get("artifact_language") or "python")
        code = _source_path_for_artifact(generation_path.parent, artifact_language).read_text(
            encoding="utf-8"
        )
        result = evaluate_code(
            task=task,
            code=code,
            variant=str(payload["variant"]),
            provider=str(payload["provider"]),
            model=str(payload["model"]),
            sample_index=int(payload.get("sample_index", 0)),
            requested_temperature=_optional_float(payload.get("requested_temperature")),
            effective_temperature=_optional_float(payload.get("effective_temperature")),
            oracle_spec=str(payload.get("oracle_spec") or oracle_spec_for_task(task)),
            oracle_spec_label=str(payload.get("oracle_spec_label") or oracle_spec_label_for_task(task)),
            pytest_timeout_seconds=pytest_timeout_seconds,
            judge_settings=judge_settings,
            judge_client=judge_client,
            hybrid=dict(payload["hybrid"]) if isinstance(payload.get("hybrid"), dict) else None,
            artifact_language=artifact_language,
            metadata=dict(payload["metadata"]) if isinstance(payload.get("metadata"), dict) else None,
            artifact_dir=generation_path.parent,
        )
        write_evaluation_result(result, generation_path.parent)
        results.append(result)
    return results


def evaluate_generation_results(
    *,
    generated: Iterable[GenerationResult],
    task_map: dict[str, Task],
    out_dir: Path,
    pytest_timeout_seconds: float,
    judge_settings: ModelSettings | None,
    judge_client: Any,
) -> list[EvaluationResult]:
    results: list[EvaluationResult] = []
    for generation in generated:
        task = task_map[generation.task_id]
        artifact_dir = _artifact_dir(
            out_dir=out_dir,
            task_id=generation.task_id,
            variant=generation.variant,
            provider=generation.provider,
            model=generation.model,
            sample_index=generation.sample_index,
        )
        result = evaluate_code(
            task=task,
            code=generation.code,
            variant=generation.variant,
            provider=generation.provider,
            model=generation.model,
            sample_index=generation.sample_index,
            requested_temperature=generation.requested_temperature,
            effective_temperature=generation.effective_temperature,
            oracle_spec=generation.oracle_spec,
            oracle_spec_label=generation.oracle_spec_label,
            pytest_timeout_seconds=pytest_timeout_seconds,
            judge_settings=judge_settings,
            judge_client=judge_client,
            hybrid=generation.hybrid,
            artifact_language=generation.artifact_language,
            metadata=generation.metadata,
            artifact_dir=artifact_dir,
        )
        write_evaluation_result(result, artifact_dir)
        results.append(result)
    return results


def evaluate_human_references(
    *,
    tasks: Iterable[Task],
    out_dir: Path,
    pytest_timeout_seconds: float,
    judge_settings: ModelSettings | None,
    judge_client: Any,
    skip_keys: set[tuple[str, str, str, str, int]] | None = None,
) -> list[EvaluationResult]:
    results: list[EvaluationResult] = []
    skipped = skip_keys or set()
    for task in tasks:
        key = _summary_key(
            task_id=task.id,
            variant="human_reference",
            provider="human",
            model="expert",
            sample_index=0,
        )
        if key in skipped:
            continue
        artifact_dir = write_human_reference_artifact(task, out_dir)
        result = evaluate_code(
            task=task,
            code=task.human_reference,
            variant="human_reference",
            provider="human",
            model="expert",
            sample_index=0,
            requested_temperature=None,
            effective_temperature=None,
            oracle_spec=oracle_spec_for_task(task),
            oracle_spec_label=oracle_spec_label_for_task(task),
            pytest_timeout_seconds=pytest_timeout_seconds,
            judge_settings=judge_settings,
            judge_client=judge_client,
            artifact_language="python",
            metadata=None,
            artifact_dir=artifact_dir,
        )
        write_evaluation_result(result, artifact_dir)
        results.append(result)
    return results


def write_evaluation_result(result: EvaluationResult, artifact_dir: Path) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "evaluation.json").write_text(
        json.dumps(result.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_summary(
    results: Iterable[EvaluationResult],
    path: Path,
    *,
    stress_results: Iterable[StressResult] | None = None,
) -> None:
    stress_by_key = {
        _summary_key(
            task_id=result.task_id,
            variant=result.variant,
            provider=result.provider,
            model=result.model,
            sample_index=result.sample_index,
        ): result
        for result in (stress_results or ())
    }
    rows: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str, str, str, int]] = set()

    for result in results:
        key = _summary_key(
            task_id=result.task_id,
            variant=result.variant,
            provider=result.provider,
            model=result.model,
            sample_index=result.sample_index,
        )
        seen_keys.add(key)
        stress = stress_by_key.get(key)
        hybrid = result.hybrid or {}
        rows.append(
            {
                "task_id": result.task_id,
                "variant": result.variant,
                "provider": result.provider,
                "model": result.model,
                "sample_index": result.sample_index,
                "requested_temperature": result.requested_temperature,
                "effective_temperature": result.effective_temperature,
                "artifact_language": result.artifact_language,
                "oracle_spec_label": result.oracle_spec_label,
                "oracle_spec": result.oracle_spec,
                "syntax_ok": result.static_metrics.syntax_ok,
                "loc": result.static_metrics.loc,
                "function_count": result.static_metrics.function_count,
                "class_count": result.static_metrics.class_count,
                "cc_total": result.static_metrics.cyclomatic_complexity_total,
                "cc_average": result.static_metrics.cyclomatic_complexity_average,
                "cc_max": result.static_metrics.cyclomatic_complexity_max,
                "maintainability_index": result.static_metrics.maintainability_index,
                "max_nesting_depth": result.static_metrics.max_nesting_depth,
                "pytest_passed": result.pytest.passed,
                "pytest_timed_out": result.pytest.timed_out,
                "judge_score": result.judge.score,
                "judge_skipped": result.judge.skipped,
                "stress_passed": stress.pass_at_1 if stress else "",
                "maintenance_token_overhead": (
                    stress.maintenance_token_overhead if stress else ""
                ),
                "maintenance_failure_type": stress.maintenance_failure_type if stress else "",
                "maintenance_failure_detail": stress.maintenance_failure_detail if stress else "",
                "context_ablation_pass_at_1": (
                    stress.context_ablation_pass_at_1
                    if stress and stress.context_ablation_pass_at_1 is not None
                    else ""
                ),
                "context_ablation_token_overhead": (
                    stress.context_ablation_token_overhead
                    if stress and stress.context_ablation_token_overhead is not None
                    else ""
                ),
                "context_ablation_failure_type": (
                    stress.context_ablation_failure_type
                    if stress and stress.context_ablation_failure_type is not None
                    else ""
                ),
                "context_ablation_failure_detail": (
                    stress.context_ablation_failure_detail
                    if stress and stress.context_ablation_failure_detail is not None
                    else ""
                ),
                "stress_duration_seconds": stress.duration_seconds if stress else "",
                "hybrid_retries": hybrid.get("hybrid_retries", ""),
                "hybrid_gate_pass": hybrid.get("hybrid_gate_pass", ""),
                "hard_cc_pass": hybrid.get("hard_cc_pass", ""),
                "hard_nesting_pass": hybrid.get("hard_nesting_pass", ""),
                "hard_pytest_pass": hybrid.get("hard_pytest_pass", ""),
                "hybrid_feedback_cc_delta": hybrid.get("hybrid_feedback_cc_delta", ""),
                "max_retries_exceeded": hybrid.get("max_retries_exceeded", ""),
                **_summary_metadata_fields(result.metadata),
                **_summary_dafny_fields(result.dafny),
            }
        )

    for key, stress in stress_by_key.items():
        if key in seen_keys:
            continue
        rows.append(
            {
                "task_id": stress.task_id,
                "variant": stress.variant,
                "provider": stress.provider,
                "model": stress.model,
                "sample_index": stress.sample_index,
                "requested_temperature": stress.requested_temperature,
                "effective_temperature": stress.effective_temperature,
                "artifact_language": "",
                "oracle_spec_label": stress.oracle_spec_label,
                "oracle_spec": stress.oracle_spec,
                "syntax_ok": "",
                "loc": "",
                "function_count": "",
                "class_count": "",
                "cc_total": "",
                "cc_average": "",
                "cc_max": "",
                "maintainability_index": "",
                "max_nesting_depth": "",
                "pytest_passed": "",
                "pytest_timed_out": "",
                "judge_score": "",
                "judge_skipped": "",
                "stress_passed": stress.pass_at_1,
                "maintenance_token_overhead": stress.maintenance_token_overhead,
                "maintenance_failure_type": stress.maintenance_failure_type,
                "maintenance_failure_detail": stress.maintenance_failure_detail,
                "context_ablation_pass_at_1": (
                    stress.context_ablation_pass_at_1
                    if stress.context_ablation_pass_at_1 is not None
                    else ""
                ),
                "context_ablation_token_overhead": (
                    stress.context_ablation_token_overhead
                    if stress.context_ablation_token_overhead is not None
                    else ""
                ),
                "context_ablation_failure_type": stress.context_ablation_failure_type or "",
                "context_ablation_failure_detail": stress.context_ablation_failure_detail or "",
                "stress_duration_seconds": stress.duration_seconds,
                "hybrid_retries": "",
                "hybrid_gate_pass": "",
                "hard_cc_pass": "",
                "hard_nesting_pass": "",
                "hard_pytest_pass": "",
                "hybrid_feedback_cc_delta": "",
                "max_retries_exceeded": "",
                **_empty_metadata_summary_fields(),
                **_empty_dafny_summary_fields(),
            }
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=_SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_chain_summary(results: Iterable[ChainStepResult], run_dir: Path) -> None:
    rows = [result.to_json_dict() for result in results]
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "chain_results.json").write_text(
        json.dumps(rows, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    fields = [
        "step",
        "task_id",
        "variant",
        "provider",
        "model",
        "sample_index",
        "maintenance_provider",
        "maintenance_model",
        "pass_bool",
        "token_estimate",
        "cc_average",
        "nesting_depth",
        "function_count",
        "elapsed_seconds",
        "accumulated_score",
        "failure_type",
        "failure_detail",
    ]
    with (run_dir / "chain_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def load_evaluation_results(run_dir: Path) -> list[EvaluationResult]:
    results: list[EvaluationResult] = []
    for evaluation_path in sorted(run_dir.rglob("evaluation.json")):
        payload = json.loads(evaluation_path.read_text(encoding="utf-8"))
        pytest_payload = dict(payload["pytest"])
        pytest_payload.setdefault("sandbox", "unknown")
        pytest_payload.setdefault("sandbox_error", None)
        judge_payload = dict(payload["judge"])
        judge_payload["strengths"] = tuple(judge_payload.get("strengths", ()))
        judge_payload["weaknesses"] = tuple(judge_payload.get("weaknesses", ()))
        results.append(
            EvaluationResult(
                task_id=str(payload["task_id"]),
                variant=str(payload["variant"]),
                provider=str(payload["provider"]),
                model=str(payload["model"]),
                sample_index=int(payload.get("sample_index", 0)),
                requested_temperature=_optional_float(payload.get("requested_temperature")),
                effective_temperature=_optional_float(payload.get("effective_temperature")),
                oracle_spec=str(payload.get("oracle_spec") or ""),
                oracle_spec_label=str(payload.get("oracle_spec_label") or ""),
                static_metrics=StaticMetrics(**payload["static_metrics"]),
                pytest=PytestResult(**pytest_payload),
                judge=JudgeResult(**judge_payload),
                artifact_language=str(payload.get("artifact_language") or "python"),
                hybrid=dict(payload["hybrid"]) if isinstance(payload.get("hybrid"), dict) else None,
                metadata=dict(payload["metadata"]) if isinstance(payload.get("metadata"), dict) else None,
                dafny=dict(payload["dafny"]) if isinstance(payload.get("dafny"), dict) else None,
            )
        )
    return results


def load_stress_results(run_dir: Path) -> list[StressResult]:
    return [
        stress_result_from_mapping(json.loads(path.read_text(encoding="utf-8")))
        for path in sorted(run_dir.rglob("stress.json"))
    ]


def validate_run_dir(
    *,
    run_dir: Path,
    tasks: Iterable[Task],
    samples: int,
    context_ablation: bool = False,
) -> list[str]:
    task_ids = {task.id for task in tasks}
    errors: list[str] = []
    generation_records = [
        (path, json.loads(path.read_text(encoding="utf-8")))
        for path in sorted(run_dir.rglob("generation.json"))
    ]
    generation_payloads = [payload for _, payload in generation_records]
    evaluation_records = [
        (path, json.loads(path.read_text(encoding="utf-8")))
        for path in sorted(run_dir.rglob("evaluation.json"))
    ]
    evaluation_payloads = [payload for _, payload in evaluation_records]
    stress_payloads = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(run_dir.rglob("stress.json"))
    ]

    generation_keys = {_payload_key(payload) for payload in generation_payloads}
    evaluation_keys = {_payload_key(payload) for payload in evaluation_payloads}
    stress_keys = {_payload_key(payload) for payload in stress_payloads}

    if generation_keys != evaluation_keys:
        errors.append("generation/evaluation artifact keys differ")
    if stress_payloads and stress_keys != evaluation_keys:
        errors.append("stress/evaluation artifact keys differ")

    evaluation_by_key = {_payload_key(payload): (path, payload) for path, payload in evaluation_records}
    for generation_path, payload in generation_records:
        artifact_language = str(payload.get("artifact_language") or "python")
        source_path = _source_path_for_artifact(generation_path.parent, artifact_language)
        if not source_path.exists():
            errors.append(f"missing source artifact: {source_path}")
        if artifact_language == "dafny":
            _, evaluation = evaluation_by_key.get(_payload_key(payload), (None, {}))
            dafny = evaluation.get("dafny") if isinstance(evaluation, dict) else None
            status = dafny.get("status") if isinstance(dafny, dict) else None
            if not status:
                errors.append(f"missing dafny_status for {generation_path.parent}")
            elif status in {"verified", "runtime_failed"} and not (generation_path.parent / "solution.py").exists():
                errors.append(f"missing compiled solution.py for {generation_path.parent}")

    human_by_task: dict[str, list[int]] = {task_id: [] for task_id in task_ids}
    generated_by_task_variant: dict[tuple[str, str], set[int]] = {}
    for payload in generation_payloads:
        task_id = str(payload["task_id"])
        variant = str(payload["variant"])
        sample_index = int(payload.get("sample_index", 0))
        if task_id not in task_ids:
            errors.append(f"unknown task in artifact: {task_id}")
        if variant == "human_reference":
            human_by_task.setdefault(task_id, []).append(sample_index)
        else:
            generated_by_task_variant.setdefault((task_id, variant), set()).add(sample_index)
            if payload.get("requested_temperature") == "":
                errors.append(f"missing requested_temperature for {task_id}/{variant}/s{sample_index}")
            if payload.get("effective_temperature") == "":
                errors.append(f"missing effective_temperature for {task_id}/{variant}/s{sample_index}")

    for task_id in sorted(task_ids):
        if sorted(human_by_task.get(task_id, [])) != [0]:
            errors.append(f"human_reference must appear once at sample_index=0 for {task_id}")

    observed_variants = {
        variant
        for (_, variant) in generated_by_task_variant
        if variant != "human_reference"
    }
    expected_samples = set(range(samples))
    for task_id in sorted(task_ids):
        for variant in sorted(observed_variants):
            actual = generated_by_task_variant.get((task_id, variant), set())
            if actual != expected_samples:
                errors.append(
                    f"{task_id}/{variant} samples {sorted(actual)} != {sorted(expected_samples)}"
                )

    if context_ablation:
        for payload in stress_payloads:
            if payload.get("context_ablation_pass_at_1") is None:
                errors.append(
                    "missing context_ablation_pass_at_1 for "
                    f"{payload.get('task_id')}/{payload.get('variant')}/"
                    f"s{payload.get('sample_index', 0)}"
                )

    summary_path = run_dir / "summary.csv"
    if summary_path.exists():
        with summary_path.open(newline="", encoding="utf-8") as handle:
            summary_rows = list(csv.DictReader(handle))
        if len(summary_rows) != len(evaluation_payloads):
            errors.append(
                f"summary rows {len(summary_rows)} != evaluation artifacts {len(evaluation_payloads)}"
            )
    else:
        errors.append("missing summary.csv")

    return errors


def validate_dataset(dataset_path: Path, *, tasks: Iterable[Task]) -> list[str]:
    task_list = list(tasks)
    errors: list[str] = []

    if not task_list:
        errors.append("dataset contains no tasks")

    task_counts: dict[str, int] = {}
    for task in task_list:
        task_counts[task.id] = task_counts.get(task.id, 0) + 1
    for task_id, count in sorted(task_counts.items()):
        if count > 1:
            errors.append(f"duplicate task id: {task_id}")

    design_notes_path = dataset_path.parent / "DESIGN_NOTES.md"
    design_notes = (
        design_notes_path.read_text(encoding="utf-8") if design_notes_path.exists() else ""
    )
    if not design_notes:
        errors.append(f"missing design notes: {design_notes_path}")

    custom_spec_count = 0
    for task in task_list:
        if not task.day2_stressors:
            errors.append(f"{task.id}: missing day2_stressors")
        for stressor in task.day2_stressors:
            if f"`{stressor}`" not in design_notes:
                errors.append(f"{task.id}: undocumented day2_stressor {stressor}")

        if "day2-hard" in task.tags and len(task.day2_stressors) < 2:
            errors.append(f"{task.id}: day2-hard requires at least two stressors")
        if len(task.day2_stressors) >= 2 and "day2-hard" not in task.tags:
            print(f"validation warning: {task.id} has 2+ stressors but lacks day2-hard")

        if task.custom_spec_override:
            custom_spec_count += 1

        if not task.human_reference.strip():
            errors.append(f"{task.id}: empty human_reference")
        if not (task.mock_solution or "").strip():
            errors.append(f"{task.id}: empty mock_solution")
        if not (task.mock_day2_solution or "").strip():
            errors.append(f"{task.id}: empty mock_day2_solution")
        copied_pilot_task = dataset_path.name == "slopbench" and task.id in _SLOPBENCH_MIN_TASK_IDS
        if (
            not copied_pilot_task
            and task.mock_solution
            and task.mock_solution.strip() == task.human_reference.strip()
        ):
            errors.append(f"{task.id}: mock_solution must differ from human_reference")
        if (
            not copied_pilot_task
            and task.mock_day2_solution
            and task.mock_day2_solution.strip() == task.human_reference.strip()
        ):
            errors.append(f"{task.id}: mock_day2_solution must differ from human_reference")

    task_by_id = {task.id: task for task in task_list}
    if dataset_path.name == "slopbench":
        if len(task_list) != 50:
            errors.append(f"slopbench must contain 50 tasks, found {len(task_list)}")
        if custom_spec_count < 8:
            errors.append(
                f"slopbench must contain at least 8 custom-spec tasks, found {custom_spec_count}"
            )

        for task_id in (
            "audit_trail_builder",
            "financial_reconciler",
            "access_control_log",
            "medical_intake_form",
            "adversarial_spec",
            "state_diff_tracker",
            "circuit_breaker",
        ):
            task = task_by_id.get(task_id)
            if task is None:
                errors.append(f"slopbench missing required custom-spec task: {task_id}")
            elif not task.custom_spec_override:
                errors.append(f"{task_id}: missing custom_spec_override")

        adversarial = task_by_id.get("adversarial_spec")
        if adversarial:
            if "adversarial_spec" not in adversarial.tags:
                errors.append("adversarial_spec: missing adversarial_spec tag")
            if "custom_spec" not in adversarial.tags:
                errors.append("adversarial_spec: missing custom_spec tag")

    return errors


def _settings_from_args(args: argparse.Namespace, *, role: str) -> ModelSettings:
    provider = _as_provider(args.provider)
    settings = default_model_settings(provider, role=role)  # type: ignore[arg-type]
    return ModelSettings(
        provider=provider,
        model=args.model or settings.model,
        temperature=args.temperature if args.temperature is not None else settings.temperature,
        max_tokens=args.max_tokens if args.max_tokens is not None else settings.max_tokens,
        timeout_seconds=args.llm_timeout if args.llm_timeout is not None else settings.timeout_seconds,
        api_key_env=settings.api_key_env,
        require_temperature=bool(getattr(args, "require_temperature", False)),
    )


def _hybrid_constraints_from_args(args: argparse.Namespace) -> HybridConstraints:
    return HybridConstraints(
        max_cc=getattr(args, "max_cc", None),
        max_nesting=getattr(args, "max_nesting", None),
        require_pytest=bool(getattr(args, "hybrid_require_pytest", True)),
        max_retries=int(getattr(args, "hybrid_max_retries", 3)),
    )


def _judge_from_args(args: argparse.Namespace) -> tuple[ModelSettings | None, Any]:
    if args.judge_provider == "none":
        return None, None

    provider = _as_provider(args.judge_provider)
    settings = default_model_settings(provider, role="judge")
    settings = ModelSettings(
        provider=provider,
        model=args.judge_model or settings.model,
        temperature=(
            args.judge_temperature if args.judge_temperature is not None else settings.temperature
        ),
        max_tokens=args.judge_max_tokens if args.judge_max_tokens is not None else settings.max_tokens,
        timeout_seconds=args.judge_timeout if args.judge_timeout is not None else settings.timeout_seconds,
        api_key_env=settings.api_key_env,
        require_temperature=False,
    )
    return settings, build_llm_client(settings)


def _artifact_dir(
    out_dir: Path,
    *,
    task_id: str,
    variant: str,
    provider: str,
    model: str,
    sample_index: int = 0,
) -> Path:
    artifact_name = (
        f"{_safe_slug(variant)}__{_safe_slug(provider)}__{_safe_slug(model)}"
        f"__s{sample_index:02d}"
    )
    return out_dir / _safe_slug(task_id) / artifact_name


def _source_path_for_artifact(artifact_dir: Path, artifact_language: str) -> Path:
    if artifact_language == "dafny":
        return artifact_dir / "solution.dfy"
    return artifact_dir / "solution.py"


def _summary_key(
    *,
    task_id: str,
    variant: str,
    provider: str,
    model: str,
    sample_index: int = 0,
) -> tuple[str, str, str, str, int]:
    return task_id, variant, provider, model, sample_index


def _payload_key(payload: dict[str, Any]) -> tuple[str, str, str, str, int]:
    return _summary_key(
        task_id=str(payload["task_id"]),
        variant=str(payload["variant"]),
        provider=str(payload["provider"]),
        model=str(payload["model"]),
        sample_index=int(payload.get("sample_index", 0)),
    )


def _safe_slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "artifact"


def _as_provider(value: str) -> Provider:
    if value in {"openai", "anthropic", "google", "mock"}:
        return value  # type: ignore[return-value]
    raise ValueError(f"unknown provider: {value}")


def _as_generation_mode(value: str) -> GenerationMode:
    if value in {
        "baseline",
        "oracle",
        "oracle_karpathy",
        "oracle_dafny",
        "neutral_style",
        "hybrid",
        "modular_discovery",
    }:
        return value  # type: ignore[return-value]
    raise ValueError(f"unknown generation mode: {value}")


def _optional_float(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    return float(value)


def _summary_metadata_fields(metadata: dict[str, Any] | None) -> dict[str, Any]:
    token_estimates = metadata.get("token_estimates") if isinstance(metadata, dict) else None
    modular = metadata.get("modular_discovery") if isinstance(metadata, dict) else None
    if not isinstance(token_estimates, dict):
        token_estimates = {}
    if not isinstance(modular, dict):
        modular = {}
    selected = modular.get("selected_skill_ids") if isinstance(modular, dict) else []
    if not isinstance(selected, list):
        selected = []
    return {
        "selected_skill_ids": ",".join(str(item) for item in selected),
        "tool_call_count": modular.get("tool_call_count", ""),
        "total_prompt_token_estimate": token_estimates.get("prompt", ""),
        "total_completion_token_estimate": token_estimates.get("completion", ""),
        "total_generation_token_estimate": token_estimates.get("total", ""),
        "generation_turn_count": len(token_estimates.get("turns", []) or []),
    }


def _empty_metadata_summary_fields() -> dict[str, str]:
    return {
        "selected_skill_ids": "",
        "tool_call_count": "",
        "total_prompt_token_estimate": "",
        "total_completion_token_estimate": "",
        "total_generation_token_estimate": "",
        "generation_turn_count": "",
    }


def _summary_dafny_fields(dafny: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(dafny, dict):
        return _empty_dafny_summary_fields()
    return {
        "dafny_status": dafny.get("status", "not_dafny"),
        "dafny_verified": dafny.get("verified", ""),
        "dafny_error_count": dafny.get("error_count", ""),
        "dafny_verification_status": dafny.get("verification_status", ""),
        "dafny_compilation_status": dafny.get("compilation_status", ""),
        "compiled_python_path": dafny.get("compiled_python_path", ""),
        "lexical_proof_complexity": dafny.get("lexical_proof_complexity", ""),
        "requires_count": dafny.get("requires_count", ""),
        "ensures_count": dafny.get("ensures_count", ""),
        "invariant_count": dafny.get("invariant_count", ""),
        "source_loc": dafny.get("source_loc", ""),
        "source_token_estimate": dafny.get("source_token_estimate", ""),
        "compiled_loc": dafny.get("compiled_loc", ""),
        "compiled_token_estimate": dafny.get("compiled_token_estimate", ""),
        "compiled_cc_average": dafny.get("compiled_cc_average", ""),
        "compiled_bloat_token_ratio": dafny.get("compiled_bloat_token_ratio", ""),
    }


def _empty_dafny_summary_fields() -> dict[str, str]:
    return {
        "dafny_status": "",
        "dafny_verified": "",
        "dafny_error_count": "",
        "dafny_verification_status": "",
        "dafny_compilation_status": "",
        "compiled_python_path": "",
        "lexical_proof_complexity": "",
        "requires_count": "",
        "ensures_count": "",
        "invariant_count": "",
        "source_loc": "",
        "source_token_estimate": "",
        "compiled_loc": "",
        "compiled_token_estimate": "",
        "compiled_cc_average": "",
        "compiled_bloat_token_ratio": "",
    }


_SUMMARY_FIELDS = [
    "task_id",
    "variant",
    "provider",
    "model",
    "sample_index",
    "requested_temperature",
    "effective_temperature",
    "artifact_language",
    "oracle_spec_label",
    "oracle_spec",
    "syntax_ok",
    "loc",
    "function_count",
    "class_count",
    "cc_total",
    "cc_average",
    "cc_max",
    "maintainability_index",
    "max_nesting_depth",
    "pytest_passed",
    "pytest_timed_out",
    "judge_score",
    "judge_skipped",
    "stress_passed",
    "maintenance_token_overhead",
    "maintenance_failure_type",
    "maintenance_failure_detail",
    "context_ablation_pass_at_1",
    "context_ablation_token_overhead",
    "context_ablation_failure_type",
    "context_ablation_failure_detail",
    "stress_duration_seconds",
    "hybrid_retries",
    "hybrid_gate_pass",
    "hard_cc_pass",
    "hard_nesting_pass",
    "hard_pytest_pass",
    "hybrid_feedback_cc_delta",
    "max_retries_exceeded",
    "selected_skill_ids",
    "tool_call_count",
    "total_prompt_token_estimate",
    "total_completion_token_estimate",
    "total_generation_token_estimate",
    "generation_turn_count",
    "dafny_status",
    "dafny_verified",
    "dafny_error_count",
    "dafny_verification_status",
    "dafny_compilation_status",
    "compiled_python_path",
    "lexical_proof_complexity",
    "requires_count",
    "ensures_count",
    "invariant_count",
    "source_loc",
    "source_token_estimate",
    "compiled_loc",
    "compiled_token_estimate",
    "compiled_cc_average",
    "compiled_bloat_token_ratio",
]


if __name__ == "__main__":
    raise SystemExit(main())
