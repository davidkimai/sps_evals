from __future__ import annotations

import ast
import json
import os
import re
import shlex
import shutil
import subprocess
import statistics
import tempfile
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from radon.complexity import cc_visit
from radon.metrics import mi_visit

from specoracle.config import (
    JUDGE_SYSTEM_PROMPT,
    JUDGE_USER_TEMPLATE,
    ModelSettings,
    Task,
    oracle_spec_for_task,
    oracle_spec_label_for_task,
)
from specoracle.generator import LLMClient

DEFAULT_PYTEST_DOCKER_IMAGE = "specoracle-pytest-dafny:py311-dotnet8"
PYTEST_SANDBOX_BASE_IMAGE = "mcr.microsoft.com/dotnet/sdk:8.0-bookworm-slim"
PYTEST_SANDBOX_PYTEST_VERSION = "9.0.2"
PYTEST_SANDBOX_DAFNY_VERSION = "4.*"
PYTEST_DOCKERFILE = """\
FROM mcr.microsoft.com/dotnet/sdk:8.0-bookworm-slim
ARG PYTEST_VERSION=9.0.2
ARG DAFNY_VERSION=4.*
ENV PYTHONDONTWRITEBYTECODE=1
ENV DOTNET_CLI_TELEMETRY_OPTOUT=1
ENV DOTNET_NOLOGO=1
ENV PATH="/root/.dotnet/tools:${PATH}"
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates python3 python3-pip python3-z3 z3 \
    && ln -sf /usr/bin/python3 /usr/local/bin/python \
    && rm -rf /var/lib/apt/lists/*
RUN python3 -m pip install --break-system-packages --no-cache-dir \
    pytest==${PYTEST_VERSION} \
    pytest-timeout \
    jsonschema \
    deepdiff \
    pyyaml \
    numpy \
    pandas \
    DafnyRuntimePython
RUN dotnet tool install --global dafny --version "${DAFNY_VERSION}"
RUN python -m pytest --version && python -c "import z3" && z3 --version && dafny --version
WORKDIR /work
"""

DAFNY_STATUSES = frozenset(
    {
        "not_dafny",
        "verified",
        "verification_failed",
        "compilation_failed",
        "runtime_failed",
        "language_mismatch",
        "invalid_dafny_output",
    }
)
_DAFNY_KEYWORDS = (
    "if",
    "while",
    "match",
    "forall",
    "exists",
    "assert",
    "assume",
    "requires",
    "ensures",
    "invariant",
    "decreases",
)


class CompletedProcessLike:
    returncode: int
    stdout: str | bytes | None
    stderr: str | bytes | None


DafnyRunner = Callable[[Sequence[str], float], CompletedProcessLike]


@dataclass(frozen=True)
class StaticMetrics:
    syntax_ok: bool
    syntax_error: str | None
    loc: int
    function_count: int
    class_count: int
    cyclomatic_complexity_total: int
    cyclomatic_complexity_average: float
    cyclomatic_complexity_max: int
    maintainability_index: float | None
    max_nesting_depth: int


@dataclass(frozen=True)
class PytestResult:
    passed: bool
    exit_code: int
    duration_seconds: float
    timed_out: bool
    sandbox: str
    stdout: str
    stderr: str
    sandbox_error: str | None = None


@dataclass(frozen=True)
class DafnyVerificationResult:
    verified: bool
    status: str
    exit_code: int
    duration_seconds: float
    timed_out: bool
    sandbox: str
    command: tuple[str, ...]
    stdout: str
    stderr: str
    verified_count: int | None = None
    error_count: int | None = None
    sandbox_error: str | None = None


@dataclass(frozen=True)
class DafnyCompilationResult:
    translated: bool
    status: str
    exit_code: int
    duration_seconds: float
    timed_out: bool
    sandbox: str
    command: tuple[str, ...]
    stdout: str
    stderr: str
    compiled_python: str
    compiled_python_path: str | None
    compiled_static_metrics: StaticMetrics | None
    support_files: tuple[tuple[str, str], ...] = ()
    verified_count: int | None = None
    error_count: int | None = None
    sandbox_error: str | None = None


@dataclass(frozen=True)
class JudgeResult:
    skipped: bool
    score: int | None
    rationale: str
    strengths: tuple[str, ...] = ()
    weaknesses: tuple[str, ...] = ()
    raw_response: str = ""
    error: str | None = None


@dataclass(frozen=True)
class EvaluationResult:
    task_id: str
    variant: str
    provider: str
    model: str
    sample_index: int
    requested_temperature: float | None
    effective_temperature: float | None
    oracle_spec: str
    oracle_spec_label: str
    static_metrics: StaticMetrics
    pytest: PytestResult
    judge: JudgeResult = field(default_factory=lambda: JudgeResult(True, None, "not requested"))
    artifact_language: str = "python"
    hybrid: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    dafny: dict[str, Any] | None = None

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


class _AstSummaryVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.function_count = 0
        self.class_count = 0

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function_count += 1
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.function_count += 1
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_count += 1
        self.generic_visit(node)


class _NestingDepthVisitor(ast.NodeVisitor):
    _CONTROL_NODES = (
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.With,
        ast.AsyncWith,
        ast.Try,
        ast.ExceptHandler,
        ast.Match,
    )

    def __init__(self) -> None:
        self.current_depth = 0
        self.max_depth = 0

    def generic_visit(self, node: ast.AST) -> None:
        if isinstance(node, self._CONTROL_NODES):
            self.current_depth += 1
            self.max_depth = max(self.max_depth, self.current_depth)
            super().generic_visit(node)
            self.current_depth -= 1
            return
        super().generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        self._visit_if(node, is_elif=False)

    def _visit_if(self, node: ast.If, *, is_elif: bool) -> None:
        if not is_elif:
            self.current_depth += 1
            self.max_depth = max(self.max_depth, self.current_depth)

        for child in node.body:
            self.visit(child)

        if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            self._visit_if(node.orelse[0], is_elif=True)
        else:
            for child in node.orelse:
                self.visit(child)

        if not is_elif:
            self.current_depth -= 1


def compute_static_metrics(code: str) -> StaticMetrics:
    loc = len([line for line in code.splitlines() if line.strip()])
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return StaticMetrics(
            syntax_ok=False,
            syntax_error=f"{exc.msg} at line {exc.lineno}",
            loc=loc,
            function_count=0,
            class_count=0,
            cyclomatic_complexity_total=0,
            cyclomatic_complexity_average=0.0,
            cyclomatic_complexity_max=0,
            maintainability_index=None,
            max_nesting_depth=0,
        )

    summary = _AstSummaryVisitor()
    summary.visit(tree)

    nesting = _NestingDepthVisitor()
    nesting.visit(tree)

    blocks = cc_visit(code)
    complexities = [int(block.complexity) for block in blocks]
    total_cc = sum(complexities)
    max_cc = max(complexities, default=0)
    avg_cc = total_cc / len(complexities) if complexities else 0.0

    return StaticMetrics(
        syntax_ok=True,
        syntax_error=None,
        loc=loc,
        function_count=summary.function_count,
        class_count=summary.class_count,
        cyclomatic_complexity_total=total_cc,
        cyclomatic_complexity_average=round(avg_cc, 3),
        cyclomatic_complexity_max=max_cc,
        maintainability_index=round(float(mi_visit(code, multi=True)), 3),
        max_nesting_depth=nesting.max_depth,
    )


def compute_dafny_lexical_metrics(dfy_code: str) -> dict[str, int]:
    """Compute a lexical proof-complexity proxy for Dafny source.

    This is not cyclomatic complexity. It deliberately avoids feeding `.dfy`
    source to Python AST/Radon tooling and instead counts proof/control tokens
    after stripping strings and comments.
    """
    stripped = _strip_dafny_comments_and_strings(dfy_code)
    keyword_counts = {
        f"{keyword}_count": len(re.findall(rf"\b{re.escape(keyword)}\b", stripped))
        for keyword in _DAFNY_KEYWORDS
    }
    and_count = stripped.count("&&")
    or_count = stripped.count("||")
    loc = len([line for line in dfy_code.splitlines() if line.strip()])
    token_estimate = _estimate_token_count(dfy_code)
    lexical_proof_complexity = sum(keyword_counts.values()) + and_count + or_count
    return {
        **keyword_counts,
        "logical_and_count": and_count,
        "logical_or_count": or_count,
        "lexical_proof_complexity": lexical_proof_complexity,
        "source_loc": loc,
        "source_token_estimate": token_estimate,
        "requires_count": keyword_counts["requires_count"],
        "ensures_count": keyword_counts["ensures_count"],
        "invariant_count": keyword_counts["invariant_count"],
    }


def _strip_dafny_comments_and_strings(code: str) -> str:
    result: list[str] = []
    i = 0
    in_line_comment = False
    in_block_comment = 0
    in_string: str | None = None
    while i < len(code):
        ch = code[i]
        nxt = code[i + 1] if i + 1 < len(code) else ""

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
                result.append(ch)
            else:
                result.append(" ")
            i += 1
            continue

        if in_block_comment:
            if ch == "/" and nxt == "*":
                in_block_comment += 1
                result.extend("  ")
                i += 2
                continue
            if ch == "*" and nxt == "/":
                in_block_comment -= 1
                result.extend("  ")
                i += 2
                continue
            result.append("\n" if ch == "\n" else " ")
            i += 1
            continue

        if in_string is not None:
            if ch == "\\" and nxt:
                result.extend("  ")
                i += 2
                continue
            if ch == in_string:
                in_string = None
            result.append("\n" if ch == "\n" else " ")
            i += 1
            continue

        if ch == "/" and nxt == "/":
            in_line_comment = True
            result.extend("  ")
            i += 2
            continue
        if ch == "/" and nxt == "*":
            in_block_comment = 1
            result.extend("  ")
            i += 2
            continue
        if ch in {'"', "'"}:
            in_string = ch
            result.append(" ")
            i += 1
            continue

        result.append(ch)
        i += 1

    return "".join(result)


def run_pytest_for_code(
    code: str,
    test_code: str,
    *,
    timeout_seconds: float = 10.0,
    docker_image: str | None = None,
    memory_limit: str = "256m",
    cpus: str = "1.0",
    support_files: dict[str, str] | None = None,
) -> PytestResult:
    return run_pytest_for_files(
        code,
        {"test_solution.py": test_code},
        timeout_seconds=timeout_seconds,
        docker_image=docker_image,
        memory_limit=memory_limit,
        cpus=cpus,
        support_files=support_files,
    )


def run_pytest_for_files(
    code: str,
    test_files: Mapping[str, str],
    *,
    timeout_seconds: float = 10.0,
    docker_image: str | None = None,
    memory_limit: str = "256m",
    cpus: str = "1.0",
    support_files: dict[str, str] | None = None,
) -> PytestResult:
    """Run pytest against solution.py and one or more test files.

    External longitudinal benchmarks may supply cumulative checkpoint tests that
    are safest as separate files. This helper keeps the reusable sandbox logic in
    the evaluator layer instead of concatenating raw tests inside benchmark
    runners, where imports, fixtures, or duplicate test names can collide.
    """
    start = time.monotonic()
    image = docker_image or os.getenv("SPECORACLE_PYTEST_IMAGE", DEFAULT_PYTEST_DOCKER_IMAGE)
    if not test_files:
        return PytestResult(
            passed=False,
            exit_code=2,
            duration_seconds=round(time.monotonic() - start, 3),
            timed_out=False,
            sandbox=f"docker:{image}",
            stdout="",
            stderr="",
            sandbox_error="no_test_files",
        )
    try:
        _ensure_docker_pytest_image(image)
    except (RuntimeError, subprocess.SubprocessError) as exc:
        return PytestResult(
            passed=False,
            exit_code=125,
            duration_seconds=round(time.monotonic() - start, 3),
            timed_out=False,
            sandbox=f"docker:{image}",
            stdout="",
            stderr="",
            sandbox_error=str(exc),
        )

    with tempfile.TemporaryDirectory(prefix="specoracle_pytest_") as temp_dir:
        temp_path = Path(temp_dir)
        solution_path = temp_path / "solution.py"
        solution_path.write_text(code, encoding="utf-8")
        pytest_paths: list[str] = []
        for relative_path, content in sorted(test_files.items()):
            test_path = _safe_pytest_relative_path(relative_path)
            output_path = temp_path / test_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
            os.chmod(output_path, 0o644)
            pytest_paths.append(str(test_path))
        for relative_path, content in (support_files or {}).items():
            support_path = temp_path / _safe_support_relative_path(relative_path)
            support_path.parent.mkdir(parents=True, exist_ok=True)
            support_path.write_text(content, encoding="utf-8")
            os.chmod(support_path, 0o644)
        os.chmod(temp_path, 0o755)
        os.chmod(solution_path, 0o644)

        command = [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--memory",
            memory_limit,
            "--cpus",
            cpus,
            "--pids-limit",
            "128",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--read-only",
            "--tmpfs",
            "/tmp:rw,nosuid,nodev,size=64m,mode=1777",
            "--user",
            "65534:65534",
            "-e",
            "HOME=/tmp",
            "-e",
            "PYTHONDONTWRITEBYTECODE=1",
            "-e",
            "PYTHONPYCACHEPREFIX=/tmp/pycache",
            "--mount",
            f"type=bind,source={temp_path},target=/work,readonly",
            "-w",
            "/work",
            image,
            "python",
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            *pytest_paths,
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return PytestResult(
                passed=False,
                exit_code=124,
                duration_seconds=round(time.monotonic() - start, 3),
                timed_out=True,
                sandbox=f"docker:{image}",
                stdout=_coerce_output(exc.stdout),
                stderr=_coerce_output(exc.stderr),
            )

    return PytestResult(
        passed=completed.returncode == 0,
        exit_code=completed.returncode,
        duration_seconds=round(time.monotonic() - start, 3),
        timed_out=False,
        sandbox=f"docker:{image}",
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


@dataclass(frozen=True)
class _ScbenchBashSpec:
    checkpoint: str
    problem_path: str
    entry_file: str
    test_files: tuple[str, ...]
    static_assets: tuple[str, ...]
    checkpoint_timeout: int


def is_scbench_bash_test(test_code: str) -> bool:
    """Return True for SCBench bash checkpoint driver scripts."""
    head = test_code.lstrip()[:512].lower()
    return head.startswith("#!/usr/bin/env bash") and "scbench test runner" in head


def run_scbench_bash_tests(
    code: str,
    test_files: Mapping[str, str],
    *,
    timeout_seconds: float = 30.0,
    docker_image: str | None = None,
    memory_limit: str = "512m",
    cpus: str = "1.0",
    problem_repo_dir: str | Path | None = None,
) -> PytestResult:
    """Run SCBench Python checkpoint tests described by bash driver scripts.

    The Hugging Face SCBench Python split stores checkpoint tests as bash
    drivers. Those scripts fetch/materialize official tests from the upstream
    `scb-problems` repository and then invoke pytest with benchmark-specific
    options. Running the bash text as a pytest `.py` file creates a false
    SyntaxError. This helper parses the driver metadata, materializes equivalent
    per-checkpoint pytest workspaces, and runs each checkpoint in the existing
    Docker sandbox without writing raw benchmark tests to tracked artifacts.
    """
    start = time.monotonic()
    image = docker_image or os.getenv("SPECORACLE_PYTEST_IMAGE", DEFAULT_PYTEST_DOCKER_IMAGE)
    if not test_files:
        return PytestResult(
            passed=False,
            exit_code=2,
            duration_seconds=round(time.monotonic() - start, 3),
            timed_out=False,
            sandbox=f"docker:{image}:scbench",
            stdout="",
            stderr="",
            sandbox_error="no_test_files",
        )

    try:
        specs = [_parse_scbench_bash_spec(content) for _, content in sorted(test_files.items())]
        repo_path = _ensure_scbench_problem_repo(
            specs,
            base_dir=Path(problem_repo_dir) if problem_repo_dir is not None else None,
        )
        _ensure_docker_pytest_image(image)
    except (RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        return PytestResult(
            passed=False,
            exit_code=125,
            duration_seconds=round(time.monotonic() - start, 3),
            timed_out=False,
            sandbox=f"docker:{image}:scbench",
            stdout="",
            stderr="",
            sandbox_error=str(exc),
        )

    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    last_exit_code = 0
    with tempfile.TemporaryDirectory(prefix="specoracle_scbench_") as temp_dir:
        temp_path = Path(temp_dir)
        for index, spec in enumerate(specs, start=1):
            workspace = temp_path / f"checkpoint_{index:03d}"
            try:
                _materialize_scbench_workspace(
                    workspace=workspace,
                    repo_path=repo_path,
                    spec=spec,
                    code=code,
                )
            except (OSError, RuntimeError, ValueError) as exc:
                return PytestResult(
                    passed=False,
                    exit_code=125,
                    duration_seconds=round(time.monotonic() - start, 3),
                    timed_out=False,
                    sandbox=f"docker:{image}:scbench",
                    stdout="\n".join(stdout_parts),
                    stderr="\n".join(stderr_parts),
                    sandbox_error=str(exc),
                )

            command = [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--memory",
                memory_limit,
                "--cpus",
                cpus,
                "--pids-limit",
                "256",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges",
                "--tmpfs",
                "/tmp:rw,nosuid,nodev,size=128m,mode=1777",
                "--user",
                "65534:65534",
                "-e",
                "HOME=/tmp",
                "-e",
                "PYTHONDONTWRITEBYTECODE=1",
                "-e",
                "PYTHONPYCACHEPREFIX=/tmp/pycache",
                "--mount",
                f"type=bind,source={workspace},target=/work",
                "-w",
                "/work",
                image,
                "python",
                "-m",
                "pytest",
                "--entrypoint",
                f"python {spec.entry_file}",
                "--checkpoint",
                spec.checkpoint,
                "--timeout",
                str(spec.checkpoint_timeout),
                "-q",
                "-p",
                "no:cacheprovider",
                "tests",
            ]
            try:
                completed = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                return PytestResult(
                    passed=False,
                    exit_code=124,
                    duration_seconds=round(time.monotonic() - start, 3),
                    timed_out=True,
                    sandbox=f"docker:{image}:scbench",
                    stdout="\n".join([*stdout_parts, _coerce_output(exc.stdout)]),
                    stderr="\n".join([*stderr_parts, _coerce_output(exc.stderr)]),
                )

            stdout_parts.append(completed.stdout)
            stderr_parts.append(completed.stderr)
            last_exit_code = completed.returncode
            if completed.returncode != 0:
                return PytestResult(
                    passed=False,
                    exit_code=completed.returncode,
                    duration_seconds=round(time.monotonic() - start, 3),
                    timed_out=False,
                    sandbox=f"docker:{image}:scbench",
                    stdout="\n".join(stdout_parts),
                    stderr="\n".join(stderr_parts),
                )

    return PytestResult(
        passed=True,
        exit_code=last_exit_code,
        duration_seconds=round(time.monotonic() - start, 3),
        timed_out=False,
        sandbox=f"docker:{image}:scbench",
        stdout="\n".join(stdout_parts),
        stderr="\n".join(stderr_parts),
    )


def _parse_scbench_bash_spec(test_code: str) -> _ScbenchBashSpec:
    if not is_scbench_bash_test(test_code):
        raise ValueError("test file is not an SCBench bash driver")
    problem_path = _parse_scbench_assignment(test_code, "PROBLEM_PATH")
    checkpoint = _parse_scbench_assignment(test_code, "CHECKPOINT")
    entry_file = _parse_scbench_assignment(test_code, "ENTRY_FILE")
    timeout_text = _parse_scbench_assignment(test_code, "CHECKPOINT_TIMEOUT", default="20")
    test_files = tuple(_parse_scbench_array(test_code, "TEST_FILES"))
    static_assets = tuple(_parse_scbench_array(test_code, "STATIC_ASSETS"))
    if not problem_path or not checkpoint or not entry_file or not test_files:
        raise ValueError("SCBench bash driver lacks required metadata")
    _safe_support_relative_path(entry_file)
    for relative_path in test_files:
        _safe_support_relative_path(relative_path)
    for asset in static_assets:
        if ":" not in asset:
            raise ValueError(f"invalid SCBench static asset spec: {asset!r}")
        name, relative_path = asset.split(":", 1)
        _safe_support_relative_path(name)
        _safe_support_relative_path(relative_path)
    try:
        checkpoint_timeout = int(timeout_text)
    except ValueError as exc:
        raise ValueError(f"invalid SCBench checkpoint timeout: {timeout_text!r}") from exc
    return _ScbenchBashSpec(
        checkpoint=checkpoint,
        problem_path=problem_path,
        entry_file=entry_file,
        test_files=test_files,
        static_assets=static_assets,
        checkpoint_timeout=checkpoint_timeout,
    )


def _parse_scbench_assignment(test_code: str, key: str, *, default: str | None = None) -> str:
    match = re.search(rf"^{re.escape(key)}=(.+)$", test_code, re.MULTILINE)
    if not match:
        if default is None:
            raise ValueError(f"SCBench bash driver lacks {key}")
        return default
    raw = match.group(1).strip()
    if raw.startswith("${"):
        if default is None:
            raise ValueError(f"unsupported dynamic SCBench assignment for {key}")
        return default
    parts = shlex.split(raw)
    return parts[0] if parts else ""


def _parse_scbench_array(test_code: str, key: str) -> list[str]:
    match = re.search(rf"^{re.escape(key)}=\((.*?)\)$", test_code, re.MULTILINE)
    if not match:
        return []
    return shlex.split(match.group(1).strip())


def _ensure_scbench_problem_repo(
    specs: Sequence[_ScbenchBashSpec],
    *,
    base_dir: Path | None = None,
) -> Path:
    repo_url = os.getenv("SCB_PROBLEMS_REPO_URL", "https://github.com/gabeorlanski/scb-problems.git")
    repo_ref = os.getenv("SCB_PROBLEMS_REPO_REF", "ba1f7fec544dae4ff274d2447d9b65aebfbc5196")
    explicit_repo = os.getenv("SCB_PROBLEMS_REPO")
    if explicit_repo:
        repo_path = Path(explicit_repo).expanduser()
        if not repo_path.exists():
            raise RuntimeError(f"SCB_PROBLEMS_REPO does not exist: {repo_path}")
    else:
        repo_path = base_dir or Path("artifacts/scbench_cache/scb-problems")
        repo_path = repo_path.expanduser()
        if not (repo_path / ".git").exists():
            repo_path.parent.mkdir(parents=True, exist_ok=True)
            cloned = subprocess.run(
                ["git", "clone", "--filter=blob:none", repo_url, str(repo_path)],
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )
            if cloned.returncode != 0:
                detail = (cloned.stderr or cloned.stdout).strip()
                raise RuntimeError(f"failed to clone SCBench problems repo: {detail}")
        fetched = subprocess.run(
            ["git", "-C", str(repo_path), "fetch", "--depth", "1", "origin", repo_ref],
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        if fetched.returncode != 0:
            # The ref may already exist locally from a previous full clone.
            has_ref = subprocess.run(
                ["git", "-C", str(repo_path), "cat-file", "-e", f"{repo_ref}^{{commit}}"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if has_ref.returncode != 0:
                detail = (fetched.stderr or fetched.stdout).strip()
                raise RuntimeError(f"failed to fetch SCBench problems ref: {detail}")
        checked_out = subprocess.run(
            ["git", "-C", str(repo_path), "checkout", "--detach", repo_ref],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if checked_out.returncode != 0:
            detail = (checked_out.stderr or checked_out.stdout).strip()
            raise RuntimeError(f"failed to checkout SCBench problems ref: {detail}")
    for spec in specs:
        tests_dir = repo_path / spec.problem_path / "tests"
        if not tests_dir.is_dir():
            raise RuntimeError(f"SCBench tests directory not found: {tests_dir}")
    return repo_path


def _materialize_scbench_workspace(
    *,
    workspace: Path,
    repo_path: Path,
    spec: _ScbenchBashSpec,
    code: str,
) -> None:
    problem_dir = repo_path / spec.problem_path
    source_tests = problem_dir / "tests"
    workspace.mkdir(parents=True, exist_ok=True)
    entry_path = workspace / _safe_support_relative_path(spec.entry_file)
    entry_path.parent.mkdir(parents=True, exist_ok=True)
    entry_path.write_text(code, encoding="utf-8")
    tests_dir = workspace / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)

    for item in source_tests.iterdir():
        if item.is_file() and not re.fullmatch(r"test_checkpoint_[0-9]+\.py", item.name):
            shutil.copy2(item, tests_dir / item.name)
    for test_file in spec.test_files:
        source = source_tests / _safe_support_relative_path(test_file)
        if not source.is_file():
            raise RuntimeError(f"selected SCBench test file not found: {source}")
        shutil.copy2(source, tests_dir / source.name)
    for item in source_tests.iterdir():
        if item.is_dir() and item.name != "__pycache__":
            shutil.copytree(item, tests_dir / item.name, dirs_exist_ok=True)

    assets_root = tests_dir / "assets"
    assets_root.mkdir(parents=True, exist_ok=True)
    for asset in spec.static_assets:
        name, relative_path = asset.split(":", 1)
        source = problem_dir / _safe_support_relative_path(relative_path)
        destination = assets_root / _safe_support_relative_path(name)
        if not source.exists():
            raise RuntimeError(f"SCBench static asset not found: {source}")
        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    (workspace / "pytest.ini").write_text(
        "[pytest]\n"
        "testpaths = tests\n"
        "markers =\n"
        "    error: error-handling / edge-case tests\n"
        "    functionality: non-core / nice-to-have tests\n"
        "    regression: regression tests from prior checkpoints\n",
        encoding="utf-8",
    )
    _chmod_tree_for_container(workspace)


def _chmod_tree_for_container(path: Path) -> None:
    for item in path.rglob("*"):
        if item.is_dir():
            os.chmod(item, 0o777)
        else:
            os.chmod(item, 0o666)
    os.chmod(path, 0o777)


def _safe_pytest_relative_path(relative_path: str) -> Path:
    path = Path(relative_path)
    if path.is_absolute() or ".." in path.parts or path.name == "":
        raise ValueError(f"unsafe pytest file path: {relative_path!r}")
    if path.suffix != ".py":
        raise ValueError(f"pytest file path must end in .py: {relative_path!r}")
    if not path.name.startswith("test_"):
        raise ValueError(f"pytest file path must start with test_: {relative_path!r}")
    return path


def _safe_support_relative_path(relative_path: str) -> Path:
    path = Path(relative_path)
    if path.is_absolute() or ".." in path.parts or path.name == "":
        raise ValueError(f"unsafe support file path: {relative_path!r}")
    return path


def verify_dafny_code(
    dfy_code: str,
    *,
    timeout_seconds: float = 30.0,
    runner: DafnyRunner | None = None,
    dafny_executable: str | None = None,
    sandbox: str = "host",
    docker_image: str | None = None,
) -> DafnyVerificationResult:
    """Verify Dafny source and return structured verifier evidence."""
    with tempfile.TemporaryDirectory(prefix="specoracle_dafny_verify_") as temp_dir:
        temp_path = Path(temp_dir)
        source_path = temp_path / "solution.dfy"
        source_path.write_text(dfy_code, encoding="utf-8")
        if sandbox == "docker":
            image = docker_image or os.getenv("SPECORACLE_DAFNY_IMAGE", DEFAULT_PYTEST_DOCKER_IMAGE)
            try:
                command = _docker_dafny_command(
                    ["dafny", "verify", "/work/solution.dfy"],
                    temp_path=temp_path,
                    image=image,
                )
            except FileNotFoundError as exc:
                return _dafny_verification_result(
                    verified=False,
                    status="tool_missing",
                    exit_code=127,
                    start=time.monotonic(),
                    command=["docker", "run", image, "dafny", "verify", "/work/solution.dfy"],
                    stdout="",
                    stderr=str(exc),
                    sandbox="docker",
                    sandbox_error=str(exc),
                )
        else:
            executable = dafny_executable or os.getenv("SPECORACLE_DAFNY", "dafny")
            if runner is None and _missing_executable(executable):
                return _dafny_verification_result(
                    verified=False,
                    status="tool_missing",
                    exit_code=127,
                    start=time.monotonic(),
                    command=[executable, "verify", str(source_path)],
                    stdout="",
                    stderr="",
                    sandbox="host",
                    sandbox_error=(
                        f"Dafny executable {executable!r} was not found on PATH. "
                        "Install Dafny locally or run the Docker sandbox with "
                        "`python3 -m specoracle.cli sandbox prepare`."
                    ),
                )
            command = [executable, "verify", str(source_path)]
        return _run_dafny_verification_command(
            command,
            timeout_seconds=timeout_seconds,
            runner=runner,
            sandbox=sandbox,
        )


def compile_dafny_to_python(
    dfy_code: str,
    *,
    timeout_seconds: float = 30.0,
    runner: DafnyRunner | None = None,
    dafny_executable: str | None = None,
    sandbox: str = "host",
    docker_image: str | None = None,
    cli_style: str = "modern",
    artifact_dir: Path | None = None,
) -> DafnyCompilationResult:
    """Translate Dafny to Python and compute metrics on the compiled Python."""
    with tempfile.TemporaryDirectory(prefix="specoracle_dafny_compile_") as temp_dir:
        temp_path = Path(temp_dir)
        source_path = temp_path / "solution.dfy"
        output_dir = temp_path / "compiled"
        output_dir.mkdir()
        output_base = output_dir / "solution"
        source_path.write_text(dfy_code, encoding="utf-8")

        if sandbox == "docker":
            image = docker_image or os.getenv("SPECORACLE_DAFNY_IMAGE", DEFAULT_PYTEST_DOCKER_IMAGE)
            inner_command = _dafny_compile_inner_command(
                source_path=Path("/work/solution.dfy"),
                output_base=Path("/work/compiled/solution"),
                executable="dafny",
                cli_style=cli_style,
            )
            try:
                command = _docker_dafny_command(
                    inner_command,
                    temp_path=temp_path,
                    image=image,
                )
            except FileNotFoundError as exc:
                return _dafny_compilation_result(
                    translated=False,
                    status="tool_missing",
                    exit_code=127,
                    start=time.monotonic(),
                    command=["docker", "run", image, *inner_command],
                    stdout="",
                    stderr=str(exc),
                    sandbox="docker",
                    compiled_python="",
                    compiled_python_path=None,
                    compiled_static_metrics=None,
                    sandbox_error=str(exc),
                )
        else:
            executable = dafny_executable or os.getenv("SPECORACLE_DAFNY", "dafny")
            command = _dafny_compile_inner_command(
                source_path=source_path,
                output_base=output_base,
                executable=executable,
                cli_style=cli_style,
            )
            if runner is None and _missing_executable(executable):
                return _dafny_compilation_result(
                    translated=False,
                    status="tool_missing",
                    exit_code=127,
                    start=time.monotonic(),
                    command=command,
                    stdout="",
                    stderr="",
                    sandbox="host",
                    compiled_python="",
                    compiled_python_path=None,
                    compiled_static_metrics=None,
                    sandbox_error=(
                        f"Dafny executable {executable!r} was not found on PATH. "
                        "Install Dafny locally or run the Docker sandbox with "
                        "`python3 -m specoracle.cli sandbox prepare`."
                    ),
                )

        start = time.monotonic()
        try:
            completed = _run_subprocess(command, timeout_seconds=timeout_seconds, runner=runner)
        except subprocess.TimeoutExpired as exc:
            return _dafny_compilation_result(
                translated=False,
                status="timeout",
                exit_code=124,
                start=start,
                command=command,
                stdout=_coerce_output(exc.stdout),
                stderr=_coerce_output(exc.stderr),
                sandbox=sandbox,
                timed_out=True,
                compiled_python="",
                compiled_python_path=None,
                compiled_static_metrics=None,
            )
        except FileNotFoundError as exc:
            return _dafny_compilation_result(
                translated=False,
                status="tool_missing",
                exit_code=127,
                start=start,
                command=command,
                stdout="",
                stderr=str(exc),
                sandbox=sandbox,
                compiled_python="",
                compiled_python_path=None,
                compiled_static_metrics=None,
                sandbox_error=str(exc),
            )

        stdout = _coerce_output(completed.stdout)
        stderr = _coerce_output(completed.stderr)
        verified_count, error_count = _parse_dafny_counts(stdout + "\n" + stderr)
        if completed.returncode != 0:
            return _dafny_compilation_result(
                translated=False,
                status="translation_failed",
                exit_code=completed.returncode,
                start=start,
                command=command,
                stdout=stdout,
                stderr=stderr,
                sandbox=sandbox,
                compiled_python="",
                compiled_python_path=None,
                compiled_static_metrics=None,
                verified_count=verified_count,
                error_count=error_count,
            )

        compiled_path = _find_compiled_python(output_dir)
        if compiled_path is None:
            return _dafny_compilation_result(
                translated=False,
                status="compiled_python_missing",
                exit_code=completed.returncode,
                start=start,
                command=command,
                stdout=stdout,
                stderr=stderr,
                sandbox=sandbox,
                compiled_python="",
                compiled_python_path=None,
                compiled_static_metrics=None,
                verified_count=verified_count,
                error_count=error_count,
            )

        support_files = _collect_dafny_support_files(compiled_path)
        compiled_python = _adapt_compiled_dafny_python(
            compiled_path.read_text(encoding="utf-8"),
            support_files=dict(support_files),
        )
        compiled_path.write_text(compiled_python, encoding="utf-8")
        persisted_path = _persist_compiled_dafny_artifacts(
            compiled_python=compiled_python,
            support_files=dict(support_files),
            artifact_dir=artifact_dir,
        )
        metrics = compute_static_metrics(compiled_python)
        return _dafny_compilation_result(
            translated=True,
            status="translated",
            exit_code=completed.returncode,
            start=start,
            command=command,
            stdout=stdout,
            stderr=stderr,
            sandbox=sandbox,
            compiled_python=compiled_python,
            compiled_python_path=str(persisted_path or compiled_path),
            compiled_static_metrics=metrics,
            support_files=support_files,
            verified_count=verified_count,
            error_count=error_count,
        )


def judge_code(
    *,
    task: Task,
    code: str,
    oracle_spec: str,
    client: LLMClient | None,
    settings: ModelSettings | None,
) -> JudgeResult:
    if client is None or settings is None:
        return JudgeResult(skipped=True, score=None, rationale="not requested")

    prompt = JUDGE_USER_TEMPLATE.format(
        task_id=task.id,
        entry_point=task.entry_point,
        prompt=task.prompt.strip(),
        oracle_spec=oracle_spec.strip(),
        code=code,
    )
    try:
        raw = client.complete(
            system_prompt=JUDGE_SYSTEM_PROMPT,
            user_prompt=prompt,
            settings=settings,
        )
        payload = _parse_judge_json(raw)
        score = int(payload["score"])
        score = min(10, max(1, score))
        return JudgeResult(
            skipped=False,
            score=score,
            rationale=str(payload.get("rationale") or ""),
            strengths=tuple(str(item) for item in payload.get("strengths", ())),
            weaknesses=tuple(str(item) for item in payload.get("weaknesses", ())),
            raw_response=raw,
            error=None,
        )
    except Exception as exc:  # Judge failures should not erase static/test evidence.
        return JudgeResult(
            skipped=False,
            score=None,
            rationale="judge failed",
            raw_response=locals().get("raw", ""),
            error=str(exc),
        )


def evaluate_code(
    *,
    task: Task,
    code: str,
    variant: str,
    provider: str,
    model: str,
    sample_index: int = 0,
    requested_temperature: float | None = None,
    effective_temperature: float | None = None,
    oracle_spec: str | None = None,
    oracle_spec_label: str | None = None,
    pytest_timeout_seconds: float,
    judge_client: LLMClient | None = None,
    judge_settings: ModelSettings | None = None,
    hybrid: dict[str, Any] | None = None,
    artifact_language: str = "python",
    metadata: dict[str, Any] | None = None,
    artifact_dir: Path | None = None,
) -> EvaluationResult:
    active_oracle_spec = oracle_spec or oracle_spec_for_task(task)
    active_oracle_label = oracle_spec_label or oracle_spec_label_for_task(task)
    if artifact_language == "dafny":
        return _evaluate_dafny_code(
            task=task,
            code=code,
            variant=variant,
            provider=provider,
            model=model,
            sample_index=sample_index,
            requested_temperature=requested_temperature,
            effective_temperature=effective_temperature,
            oracle_spec=active_oracle_spec,
            oracle_spec_label=active_oracle_label,
            pytest_timeout_seconds=pytest_timeout_seconds,
            judge_client=judge_client,
            judge_settings=judge_settings,
            hybrid=hybrid,
            metadata=metadata,
            artifact_dir=artifact_dir,
        )

    dafny_status = _python_artifact_dafny_status(metadata)
    return EvaluationResult(
        task_id=task.id,
        variant=variant,
        provider=provider,
        model=model,
        sample_index=sample_index,
        requested_temperature=requested_temperature,
        effective_temperature=effective_temperature,
        oracle_spec=active_oracle_spec,
        oracle_spec_label=active_oracle_label,
        static_metrics=compute_static_metrics(code),
        pytest=run_pytest_for_code(
            code,
            task.test_code,
            timeout_seconds=pytest_timeout_seconds,
        ),
        judge=judge_code(
            task=task,
            code=code,
            oracle_spec=active_oracle_spec,
            client=judge_client,
            settings=judge_settings,
        ),
        artifact_language="python",
        hybrid=hybrid,
        metadata=metadata,
        dafny=_not_dafny_payload(status=dafny_status),
    )


def _evaluate_dafny_code(
    *,
    task: Task,
    code: str,
    variant: str,
    provider: str,
    model: str,
    sample_index: int,
    requested_temperature: float | None,
    effective_temperature: float | None,
    oracle_spec: str,
    oracle_spec_label: str,
    pytest_timeout_seconds: float,
    judge_client: LLMClient | None,
    judge_settings: ModelSettings | None,
    hybrid: dict[str, Any] | None,
    metadata: dict[str, Any] | None,
    artifact_dir: Path | None,
) -> EvaluationResult:
    lexical = compute_dafny_lexical_metrics(code)
    if _dafny_status_hint(metadata) == "invalid_dafny_output" or not _looks_like_dafny_source(code):
        return _dafny_evaluation_result(
            task=task,
            code=code,
            variant=variant,
            provider=provider,
            model=model,
            sample_index=sample_index,
            requested_temperature=requested_temperature,
            effective_temperature=effective_temperature,
            oracle_spec=oracle_spec,
            oracle_spec_label=oracle_spec_label,
            static_metrics=_empty_static_metrics("invalid Dafny output"),
            pytest=_synthetic_pytest_result("invalid_dafny_output", "generated artifact is not Dafny source"),
            judge=judge_code(
                task=task,
                code=code,
                oracle_spec=oracle_spec,
                client=judge_client,
                settings=judge_settings,
            ),
            hybrid=hybrid,
            metadata=metadata,
            dafny=_dafny_payload(status="invalid_dafny_output", lexical=lexical),
        )

    verification = verify_dafny_code(
        code,
        timeout_seconds=pytest_timeout_seconds,
        sandbox="docker",
    )
    if not verification.verified:
        return _dafny_evaluation_result(
            task=task,
            code=code,
            variant=variant,
            provider=provider,
            model=model,
            sample_index=sample_index,
            requested_temperature=requested_temperature,
            effective_temperature=effective_temperature,
            oracle_spec=oracle_spec,
            oracle_spec_label=oracle_spec_label,
            static_metrics=_empty_static_metrics("Dafny verification failed"),
            pytest=_synthetic_pytest_result("verification_failed", verification.stderr or verification.stdout),
            judge=judge_code(
                task=task,
                code=code,
                oracle_spec=oracle_spec,
                client=judge_client,
                settings=judge_settings,
            ),
            hybrid=hybrid,
            metadata=metadata,
            dafny=_dafny_payload(
                status="verification_failed",
                lexical=lexical,
                verification=verification,
            ),
        )

    compilation = compile_dafny_to_python(
        code,
        timeout_seconds=pytest_timeout_seconds,
        sandbox="docker",
        artifact_dir=artifact_dir,
    )
    if not compilation.translated or compilation.compiled_static_metrics is None:
        return _dafny_evaluation_result(
            task=task,
            code=code,
            variant=variant,
            provider=provider,
            model=model,
            sample_index=sample_index,
            requested_temperature=requested_temperature,
            effective_temperature=effective_temperature,
            oracle_spec=oracle_spec,
            oracle_spec_label=oracle_spec_label,
            static_metrics=_empty_static_metrics("Dafny compilation failed"),
            pytest=_synthetic_pytest_result("compilation_failed", compilation.stderr or compilation.stdout),
            judge=judge_code(
                task=task,
                code=code,
                oracle_spec=oracle_spec,
                client=judge_client,
                settings=judge_settings,
            ),
            hybrid=hybrid,
            metadata=metadata,
            dafny=_dafny_payload(
                status="compilation_failed",
                lexical=lexical,
                verification=verification,
                compilation=compilation,
            ),
        )

    pytest_result = run_pytest_for_code(
        compilation.compiled_python,
        task.test_code,
        timeout_seconds=pytest_timeout_seconds,
        support_files=dict(compilation.support_files),
    )
    status = "verified" if pytest_result.passed else "runtime_failed"
    return _dafny_evaluation_result(
        task=task,
        code=compilation.compiled_python,
        variant=variant,
        provider=provider,
        model=model,
        sample_index=sample_index,
        requested_temperature=requested_temperature,
        effective_temperature=effective_temperature,
        oracle_spec=oracle_spec,
        oracle_spec_label=oracle_spec_label,
        static_metrics=compilation.compiled_static_metrics,
        pytest=pytest_result,
        judge=judge_code(
            task=task,
            code=compilation.compiled_python,
            oracle_spec=oracle_spec,
            client=judge_client,
            settings=judge_settings,
        ),
        hybrid=hybrid,
        metadata=metadata,
        dafny=_dafny_payload(
            status=status,
            lexical=lexical,
            verification=verification,
            compilation=compilation,
            pytest=pytest_result,
        ),
    )


def _parse_judge_json(raw: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start < 0 or end < start:
            raise
        payload = json.loads(raw[start : end + 1])

    if not isinstance(payload, dict):
        raise ValueError("judge response must be a JSON object")
    if "score" not in payload:
        raise ValueError("judge response is missing score")
    return payload


def _dafny_evaluation_result(
    *,
    task: Task,
    code: str,
    variant: str,
    provider: str,
    model: str,
    sample_index: int,
    requested_temperature: float | None,
    effective_temperature: float | None,
    oracle_spec: str,
    oracle_spec_label: str,
    static_metrics: StaticMetrics,
    pytest: PytestResult,
    judge: JudgeResult,
    hybrid: dict[str, Any] | None,
    metadata: dict[str, Any] | None,
    dafny: dict[str, Any],
) -> EvaluationResult:
    return EvaluationResult(
        task_id=task.id,
        variant=variant,
        provider=provider,
        model=model,
        sample_index=sample_index,
        requested_temperature=requested_temperature,
        effective_temperature=effective_temperature,
        oracle_spec=oracle_spec,
        oracle_spec_label=oracle_spec_label,
        static_metrics=static_metrics,
        pytest=pytest,
        judge=judge,
        artifact_language="dafny",
        hybrid=hybrid,
        metadata=metadata,
        dafny=dafny,
    )


def _empty_static_metrics(reason: str) -> StaticMetrics:
    return StaticMetrics(
        syntax_ok=False,
        syntax_error=reason,
        loc=0,
        function_count=0,
        class_count=0,
        cyclomatic_complexity_total=0,
        cyclomatic_complexity_average=0.0,
        cyclomatic_complexity_max=0,
        maintainability_index=None,
        max_nesting_depth=0,
    )


def _synthetic_pytest_result(status: str, detail: str) -> PytestResult:
    return PytestResult(
        passed=False,
        exit_code=1,
        duration_seconds=0.0,
        timed_out=False,
        sandbox="not_run",
        stdout="",
        stderr=_truncate(detail, 4000),
        sandbox_error=status,
    )


def _python_artifact_dafny_status(metadata: dict[str, Any] | None) -> str:
    if _dafny_status_hint(metadata) == "language_mismatch":
        return "language_mismatch"
    selected = _selected_skill_ids(metadata)
    return "language_mismatch" if any("dafny" in skill_id for skill_id in selected) else "not_dafny"


def _dafny_status_hint(metadata: dict[str, Any] | None) -> str | None:
    if not isinstance(metadata, dict):
        return None
    modular = metadata.get("modular_discovery")
    if not isinstance(modular, dict):
        return None
    raw = modular.get("dafny_status_hint")
    return str(raw) if raw else None


def _selected_skill_ids(metadata: dict[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(metadata, dict):
        return ()
    modular = metadata.get("modular_discovery")
    if not isinstance(modular, dict):
        return ()
    raw_ids = modular.get("selected_skill_ids")
    if not isinstance(raw_ids, list):
        return ()
    return tuple(str(item) for item in raw_ids)


def _not_dafny_payload(*, status: str = "not_dafny") -> dict[str, Any]:
    if status not in DAFNY_STATUSES:
        raise ValueError(f"unknown Dafny status: {status}")
    return {"status": status, "selected_skill_ids": []}


def _dafny_payload(
    *,
    status: str,
    lexical: dict[str, int],
    verification: DafnyVerificationResult | None = None,
    compilation: DafnyCompilationResult | None = None,
    pytest: PytestResult | None = None,
) -> dict[str, Any]:
    if status not in DAFNY_STATUSES:
        raise ValueError(f"unknown Dafny status: {status}")
    compiled_metrics = compilation.compiled_static_metrics if compilation else None
    compiled_token_estimate = (
        _estimate_token_count(compilation.compiled_python)
        if compilation and compilation.compiled_python
        else None
    )
    source_token_estimate = lexical.get("source_token_estimate") or 0
    bloat_ratio = (
        round(compiled_token_estimate / max(source_token_estimate, 1), 3)
        if compiled_token_estimate is not None
        else None
    )
    return {
        "status": status,
        "verified": bool(verification.verified) if verification else False,
        "verification_status": verification.status if verification else "",
        "verification_exit_code": verification.exit_code if verification else "",
        "verification_duration_seconds": verification.duration_seconds if verification else "",
        "verification_timed_out": verification.timed_out if verification else "",
        "verified_count": verification.verified_count if verification else None,
        "error_count": verification.error_count if verification else None,
        "compilation_status": compilation.status if compilation else "",
        "compilation_exit_code": compilation.exit_code if compilation else "",
        "compilation_duration_seconds": compilation.duration_seconds if compilation else "",
        "compilation_timed_out": compilation.timed_out if compilation else "",
        "compiled_python_path": compilation.compiled_python_path if compilation else None,
        "compiled_loc": compiled_metrics.loc if compiled_metrics else "",
        "compiled_cc_average": (
            compiled_metrics.cyclomatic_complexity_average if compiled_metrics else ""
        ),
        "compiled_token_estimate": compiled_token_estimate,
        "compiled_bloat_token_ratio": bloat_ratio,
        "runtime_passed": pytest.passed if pytest else "",
        "runtime_exit_code": pytest.exit_code if pytest else "",
        "runtime_timed_out": pytest.timed_out if pytest else "",
        "lexical_proof_complexity": lexical["lexical_proof_complexity"],
        "source_loc": lexical["source_loc"],
        "source_token_estimate": source_token_estimate,
        "requires_count": lexical["requires_count"],
        "ensures_count": lexical["ensures_count"],
        "invariant_count": lexical["invariant_count"],
        "logical_and_count": lexical["logical_and_count"],
        "logical_or_count": lexical["logical_or_count"],
        "keyword_counts": {
            key.removesuffix("_count"): value
            for key, value in lexical.items()
            if key.endswith("_count")
        },
    }


def _looks_like_dafny_source(code: str) -> bool:
    return bool(re.search(r"\b(method|function|predicate|lemma|datatype|class)\b", code))


def _estimate_token_count(text: str) -> int:
    return (len(text) + 3) // 4


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 15] + "\n...[truncated]"


def _coerce_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _ensure_docker_pytest_image(image: str) -> None:
    if shutil.which("docker") is None:
        raise RuntimeError("docker executable was not found on PATH")

    inspected = subprocess.run(
        ["docker", "image", "inspect", image],
        capture_output=True,
        text=True,
        check=False,
    )
    if inspected.returncode == 0:
        return

    raise RuntimeError(
        f"Docker pytest sandbox image {image!r} was not found. "
        "Run `specoracle sandbox prepare` before evaluation."
    )


def prepare_pytest_sandbox(*, image: str = DEFAULT_PYTEST_DOCKER_IMAGE) -> None:
    if shutil.which("docker") is None:
        raise RuntimeError("docker executable was not found on PATH")

    inspected = subprocess.run(
        ["docker", "image", "inspect", image],
        capture_output=True,
        text=True,
        check=False,
    )
    if inspected.returncode == 0 and _docker_image_has_sandbox_tools(image):
        return

    dockerfile_text = PYTEST_DOCKERFILE.replace(
        "mcr.microsoft.com/dotnet/sdk:8.0-bookworm-slim",
        PYTEST_SANDBOX_BASE_IMAGE,
    ).replace(
        "PYTEST_VERSION=9.0.2",
        f"PYTEST_VERSION={PYTEST_SANDBOX_PYTEST_VERSION}",
    ).replace(
        "DAFNY_VERSION=4.*",
        f"DAFNY_VERSION={PYTEST_SANDBOX_DAFNY_VERSION}",
    )
    with tempfile.TemporaryDirectory(prefix="specoracle_docker_build_") as temp_dir:
        dockerfile = Path(temp_dir) / "Dockerfile"
        dockerfile.write_text(dockerfile_text, encoding="utf-8")
        built = subprocess.run(
            ["docker", "build", "-t", image, temp_dir],
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
    if built.returncode != 0:
        detail = (built.stderr or built.stdout).strip()
        raise RuntimeError(f"failed to build Docker pytest image {image}: {detail}")


def benchmark_pytest_sandbox(
    *,
    iterations: int = 5,
    timeout_seconds: float = 10.0,
    image: str = DEFAULT_PYTEST_DOCKER_IMAGE,
) -> dict[str, float | int | str | bool]:
    durations: list[float] = []
    failures = 0
    for _ in range(iterations):
        result = run_pytest_for_code(
            "def answer():\n    return 42\n",
            "from solution import answer\n\n\ndef test_answer():\n    assert answer() == 42\n",
            timeout_seconds=timeout_seconds,
            docker_image=image,
        )
        durations.append(result.duration_seconds)
        if not result.passed:
            failures += 1

    return {
        "image": image,
        "iterations": iterations,
        "failures": failures,
        "all_passed": failures == 0,
        "median_seconds": round(statistics.median(durations), 3),
        "min_seconds": round(min(durations), 3),
        "max_seconds": round(max(durations), 3),
    }


def smoke_test_dafny_sandbox(
    *,
    timeout_seconds: float = 30.0,
    image: str = DEFAULT_PYTEST_DOCKER_IMAGE,
) -> dict[str, Any]:
    """Verify, compile, import, and pytest a tiny Dafny artifact in the sandbox."""
    prepare_pytest_sandbox(image=image)
    source = "method Main() {}\n"
    verification = verify_dafny_code(
        source,
        timeout_seconds=timeout_seconds,
        sandbox="docker",
        docker_image=image,
    )
    compilation = compile_dafny_to_python(
        source,
        timeout_seconds=timeout_seconds,
        sandbox="docker",
        docker_image=image,
    )
    pytest_result = (
        run_pytest_for_code(
            compilation.compiled_python,
            "import solution\n\n\ndef test_import_solution():\n    assert solution is not None\n",
            timeout_seconds=timeout_seconds,
            docker_image=image,
            support_files=dict(compilation.support_files),
        )
        if compilation.translated
        else _synthetic_pytest_result("compilation_failed", compilation.stderr or compilation.stdout)
    )
    return {
        "image": image,
        "verification_status": verification.status,
        "verification_passed": verification.verified,
        "compilation_status": compilation.status,
        "compilation_passed": compilation.translated,
        "pytest_passed": pytest_result.passed,
        "pytest_sandbox_error": pytest_result.sandbox_error,
        "all_passed": verification.verified and compilation.translated and pytest_result.passed,
    }


def _run_dafny_verification_command(
    command: Sequence[str],
    *,
    timeout_seconds: float,
    runner: DafnyRunner | None,
    sandbox: str,
) -> DafnyVerificationResult:
    start = time.monotonic()
    try:
        completed = _run_subprocess(command, timeout_seconds=timeout_seconds, runner=runner)
    except subprocess.TimeoutExpired as exc:
        return _dafny_verification_result(
            verified=False,
            status="timeout",
            exit_code=124,
            start=start,
            command=command,
            stdout=_coerce_output(exc.stdout),
            stderr=_coerce_output(exc.stderr),
            sandbox=sandbox,
            timed_out=True,
        )
    except FileNotFoundError as exc:
        return _dafny_verification_result(
            verified=False,
            status="tool_missing",
            exit_code=127,
            start=start,
            command=command,
            stdout="",
            stderr=str(exc),
            sandbox=sandbox,
            sandbox_error=str(exc),
        )

    stdout = _coerce_output(completed.stdout)
    stderr = _coerce_output(completed.stderr)
    verified_count, error_count = _parse_dafny_counts(stdout + "\n" + stderr)
    verified = completed.returncode == 0 and error_count in {None, 0}
    return _dafny_verification_result(
        verified=verified,
        status="verified" if verified else "verification_failed",
        exit_code=completed.returncode,
        start=start,
        command=command,
        stdout=stdout,
        stderr=stderr,
        sandbox=sandbox,
        verified_count=verified_count,
        error_count=error_count,
    )


def _run_subprocess(
    command: Sequence[str],
    *,
    timeout_seconds: float,
    runner: DafnyRunner | None,
) -> CompletedProcessLike:
    if runner is not None:
        return runner(command, timeout_seconds)
    return subprocess.run(
        list(command),
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )


def _dafny_compile_inner_command(
    *,
    source_path: Path,
    output_base: Path,
    executable: str,
    cli_style: str,
) -> list[str]:
    if cli_style == "legacy":
        return [
            executable,
            "/compile:0",
            "/spillTargetCode:1",
            "/compileTarget:py",
            f"/out:{output_base}",
            str(source_path),
        ]
    if cli_style != "modern":
        raise ValueError(f"unknown Dafny cli_style: {cli_style}")
    return [
        executable,
        "translate",
        "py",
        f"--output:{output_base}",
        str(source_path),
    ]


def _docker_dafny_command(
    inner_command: Sequence[str],
    *,
    temp_path: Path,
    image: str,
) -> list[str]:
    if shutil.which("docker") is None:
        raise FileNotFoundError("docker executable was not found on PATH")
    return [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--memory",
        "768m",
        "--cpus",
        "1.0",
        "--pids-limit",
        "256",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "-e",
        "HOME=/tmp",
        "-e",
        "DOTNET_CLI_HOME=/tmp",
        "-e",
        "PATH=/root/.dotnet/tools:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "--mount",
        f"type=bind,source={temp_path},target=/work",
        "-w",
        "/work",
        image,
        *inner_command,
    ]


def _missing_executable(executable: str) -> bool:
    if os.sep in executable:
        return not Path(executable).exists()
    return shutil.which(executable) is None


def _parse_dafny_counts(output: str) -> tuple[int | None, int | None]:
    match = re.search(r"verifier finished with\s+(\d+)\s+verified,\s+(\d+)\s+errors", output)
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def _find_compiled_python(output_dir: Path) -> Path | None:
    candidates = sorted(output_dir.rglob("*.py"))
    for path in candidates:
        if path.name == "solution.py":
            return path
    for path in candidates:
        if path.name != "DafnyRuntime.py" and "_dafny" not in path.parts:
            return path
    return candidates[0] if candidates else None


def _collect_dafny_support_files(compiled_path: Path) -> tuple[tuple[str, str], ...]:
    root = compiled_path.parent
    support: list[tuple[str, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path == compiled_path:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        support.append((path.relative_to(root).as_posix(), content))
    return tuple(support)


def _adapt_compiled_dafny_python(compiled_python: str, *, support_files: dict[str, str]) -> str:
    if "module_.py" not in support_files:
        return compiled_python
    return """\
# Dafny program compiled into Python and adapted for SlopBench imports.
import module_ as _dafny_module
from module_ import *  # noqa: F403


def _specoracle_alias_dafny_symbols(namespace):
    for obj in list(namespace.values()):
        if not isinstance(obj, type):
            continue
        original_init = getattr(obj, "__init__", None)
        constructor = getattr(obj, "ctor__", None)
        if callable(original_init) and callable(constructor):
            def __init__(self, *args, __orig=original_init, __ctor=constructor, **kwargs):
                __orig(self)
                if args or kwargs:
                    __ctor(self, *args, **kwargs)

            obj.__init__ = __init__
        for name in list(vars(obj)):
            if "__" in name and not name.startswith("__"):
                setattr(obj, name.replace("__", "_"), getattr(obj, name))

    default = namespace.get("default__")
    if default is not None:
        for name in dir(default):
            if name.startswith("_"):
                continue
            attr = getattr(default, name)
            if callable(attr):
                namespace[name.replace("__", "_")] = attr


_specoracle_alias_dafny_symbols(globals())
"""


def _persist_compiled_dafny_artifacts(
    *,
    compiled_python: str,
    support_files: dict[str, str],
    artifact_dir: Path | None,
) -> Path | None:
    if artifact_dir is None:
        return None
    artifact_dir.mkdir(parents=True, exist_ok=True)
    solution_path = artifact_dir / "solution.py"
    solution_path.write_text(compiled_python, encoding="utf-8")
    for relative_path, content in support_files.items():
        target = artifact_dir / relative_path
        if target.resolve() == solution_path.resolve():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return solution_path


def _docker_image_has_sandbox_tools(image: str) -> bool:
    checked = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            image,
            "sh",
            "-lc",
            "export PATH=/root/.dotnet/tools:$PATH; "
            "python -m pytest --version >/dev/null "
            "&& python -c 'import deepdiff, jsonschema, pytest_timeout' >/dev/null "
            "&& python -c 'import _dafny' >/dev/null "
            "&& python -c 'import z3' "
            "&& z3 --version >/dev/null "
            "&& dotnet --info >/dev/null "
            "&& dafny --version >/dev/null",
        ],
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    return checked.returncode == 0


def _dafny_verification_result(
    *,
    verified: bool,
    status: str,
    exit_code: int,
    start: float,
    command: Sequence[str],
    stdout: str,
    stderr: str,
    sandbox: str,
    timed_out: bool = False,
    verified_count: int | None = None,
    error_count: int | None = None,
    sandbox_error: str | None = None,
) -> DafnyVerificationResult:
    return DafnyVerificationResult(
        verified=verified,
        status=status,
        exit_code=exit_code,
        duration_seconds=round(time.monotonic() - start, 3),
        timed_out=timed_out,
        sandbox=sandbox,
        command=tuple(command),
        stdout=stdout,
        stderr=stderr,
        verified_count=verified_count,
        error_count=error_count,
        sandbox_error=sandbox_error,
    )


def _dafny_compilation_result(
    *,
    translated: bool,
    status: str,
    exit_code: int,
    start: float,
    command: Sequence[str],
    stdout: str,
    stderr: str,
    sandbox: str,
    compiled_python: str,
    compiled_python_path: str | None,
    compiled_static_metrics: StaticMetrics | None,
    support_files: tuple[tuple[str, str], ...] = (),
    timed_out: bool = False,
    verified_count: int | None = None,
    error_count: int | None = None,
    sandbox_error: str | None = None,
) -> DafnyCompilationResult:
    return DafnyCompilationResult(
        translated=translated,
        status=status,
        exit_code=exit_code,
        duration_seconds=round(time.monotonic() - start, 3),
        timed_out=timed_out,
        sandbox=sandbox,
        command=tuple(command),
        stdout=stdout,
        stderr=stderr,
        compiled_python=compiled_python,
        compiled_python_path=compiled_python_path,
        compiled_static_metrics=compiled_static_metrics,
        support_files=support_files,
        verified_count=verified_count,
        error_count=error_count,
        sandbox_error=sandbox_error,
    )
