from __future__ import annotations

import ast
import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

from radon.complexity import cc_visit
from radon.metrics import h_visit, mi_visit
from radon.raw import analyze as raw_analyze

METRIC_SCHEMA_VERSION = "sprint6_v1"


@dataclass(frozen=True)
class MetricRecord:
    metric_schema_version: str
    language: str
    parse_ok: bool
    parse_error: str | None
    loc: int | None
    lloc: int | None
    sloc: int | None
    comments: int | None
    comment_density: float | None
    function_count: int | None
    class_count: int | None
    cc_total: int | None
    cc_average: float | None
    cc_max: int | None
    cc_block_count: int | None
    cc_top_decile_share: float | None
    cc_concentration_note: str | None
    max_nesting_depth: int | None
    maintainability_index: float | None
    halstead_volume: float | None
    halstead_difficulty: float | None
    halstead_effort: float | None
    token_count_estimate: int
    source_token_estimate: int
    compiled_token_estimate: int | None
    compiled_bloat_token_ratio: float | None
    verbosity_ratio: float | None
    redundancy_score: float | None
    long_function_share: float | None
    lexical_proof_complexity: int | None

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


class _AstSummaryVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.function_count = 0
        self.class_count = 0
        self.function_lengths: list[int] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function_count += 1
        self._record_function_length(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.function_count += 1
        self._record_function_length(node)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_count += 1
        self.generic_visit(node)

    def _record_function_length(self, node: ast.AST) -> None:
        end_lineno = getattr(node, "end_lineno", None)
        lineno = getattr(node, "lineno", None)
        if isinstance(end_lineno, int) and isinstance(lineno, int):
            self.function_lengths.append(max(1, end_lineno - lineno + 1))


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


def build_structural_metric_record(
    code: str,
    *,
    language: str = "python",
    reference_code: str | None = None,
    compiled_python: str | None = None,
) -> dict[str, Any]:
    """Build a Sprint 6 structural metric record.

    Dafny source is never passed to Python AST/Radon tooling. When compiled
    Python is supplied for a Dafny artifact, Python metrics are computed on that
    compiled artifact while lexical proof complexity is computed on `.dfy`.
    """
    normalized_language = language.lower()
    if normalized_language == "dafny":
        return _build_dafny_record(
            dfy_code=code,
            compiled_python=compiled_python,
            reference_code=reference_code,
        ).to_dict()
    return compute_python_metrics(code, reference_code=reference_code).to_dict()


def compute_python_metrics(code: str, *, reference_code: str | None = None) -> MetricRecord:
    token_estimate = estimate_token_count(code)
    verbosity_ratio = _verbosity_ratio(code, reference_code)
    loc = _nonblank_loc(code)
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return MetricRecord(
            metric_schema_version=METRIC_SCHEMA_VERSION,
            language="python",
            parse_ok=False,
            parse_error=f"{exc.msg} at line {exc.lineno}",
            loc=loc,
            lloc=None,
            sloc=None,
            comments=None,
            comment_density=None,
            function_count=0,
            class_count=0,
            cc_total=None,
            cc_average=None,
            cc_max=None,
            cc_block_count=0,
            cc_top_decile_share=None,
            cc_concentration_note="parse_failed",
            max_nesting_depth=None,
            maintainability_index=None,
            halstead_volume=None,
            halstead_difficulty=None,
            halstead_effort=None,
            token_count_estimate=token_estimate,
            source_token_estimate=token_estimate,
            compiled_token_estimate=None,
            compiled_bloat_token_ratio=None,
            verbosity_ratio=verbosity_ratio,
            redundancy_score=None,
            long_function_share=None,
            lexical_proof_complexity=None,
        )

    summary = _AstSummaryVisitor()
    summary.visit(tree)
    nesting = _NestingDepthVisitor()
    nesting.visit(tree)
    raw = _safe_raw_metrics(code)
    halstead = _safe_halstead_metrics(code)
    complexities = [int(block.complexity) for block in cc_visit(code)]
    cc_total = sum(complexities)
    cc_block_count = len(complexities)
    long_function_share = (
        sum(1 for length in summary.function_lengths if length > 15) / len(summary.function_lengths)
        if summary.function_lengths
        else 0.0
    )
    return MetricRecord(
        metric_schema_version=METRIC_SCHEMA_VERSION,
        language="python",
        parse_ok=True,
        parse_error=None,
        loc=loc,
        lloc=raw.get("lloc"),
        sloc=raw.get("sloc"),
        comments=raw.get("comments"),
        comment_density=_comment_density(raw),
        function_count=summary.function_count,
        class_count=summary.class_count,
        cc_total=cc_total,
        cc_average=round(cc_total / cc_block_count, 3) if cc_block_count else 0.0,
        cc_max=max(complexities, default=0),
        cc_block_count=cc_block_count,
        cc_top_decile_share=_cc_top_decile_share(complexities),
        cc_concentration_note=_cc_concentration_note(complexities),
        max_nesting_depth=nesting.max_depth,
        maintainability_index=_safe_maintainability_index(code),
        halstead_volume=halstead.get("volume"),
        halstead_difficulty=halstead.get("difficulty"),
        halstead_effort=halstead.get("effort"),
        token_count_estimate=token_estimate,
        source_token_estimate=token_estimate,
        compiled_token_estimate=None,
        compiled_bloat_token_ratio=None,
        verbosity_ratio=verbosity_ratio,
        redundancy_score=_redundancy_score(tree),
        long_function_share=round(long_function_share, 6),
        lexical_proof_complexity=None,
    )


def _build_dafny_record(
    *,
    dfy_code: str,
    compiled_python: str | None,
    reference_code: str | None,
) -> MetricRecord:
    lexical = compute_dafny_lexical_complexity(dfy_code)
    if compiled_python:
        py = compute_python_metrics(compiled_python, reference_code=reference_code)
        data = py.to_dict()
        data.update(
            {
                "language": "dafny",
                "lexical_proof_complexity": lexical["lexical_proof_complexity"],
                "source_token_estimate": estimate_token_count(dfy_code),
                "compiled_token_estimate": estimate_token_count(compiled_python),
                "compiled_bloat_token_ratio": _compiled_bloat_ratio(
                    dfy_code,
                    compiled_python,
                ),
            }
        )
        return MetricRecord(**{key: data[key] for key in MetricRecord.__dataclass_fields__})
    return MetricRecord(
        metric_schema_version=METRIC_SCHEMA_VERSION,
        language="dafny",
        parse_ok=True,
        parse_error=None,
        loc=_nonblank_loc(dfy_code),
        lloc=None,
        sloc=None,
        comments=None,
        comment_density=None,
        function_count=None,
        class_count=None,
        cc_total=None,
        cc_average=None,
        cc_max=None,
        cc_block_count=None,
        cc_top_decile_share=None,
        cc_concentration_note="dafny_source_lexical_only",
        max_nesting_depth=None,
        maintainability_index=None,
        halstead_volume=None,
        halstead_difficulty=None,
        halstead_effort=None,
        token_count_estimate=estimate_token_count(dfy_code),
        source_token_estimate=estimate_token_count(dfy_code),
        compiled_token_estimate=None,
        compiled_bloat_token_ratio=None,
        verbosity_ratio=_verbosity_ratio(dfy_code, reference_code),
        redundancy_score=None,
        long_function_share=None,
        lexical_proof_complexity=lexical["lexical_proof_complexity"],
    )


def compute_dafny_lexical_complexity(dfy_code: str) -> dict[str, int]:
    stripped = _strip_dafny_comments_and_strings(dfy_code)
    keywords = (
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
    counts = {
        f"{keyword}_count": len(re.findall(rf"\b{re.escape(keyword)}\b", stripped))
        for keyword in keywords
    }
    logical_and_count = stripped.count("&&")
    logical_or_count = stripped.count("||")
    return {
        **counts,
        "logical_and_count": logical_and_count,
        "logical_or_count": logical_or_count,
        "lexical_proof_complexity": sum(counts.values()) + logical_and_count + logical_or_count,
    }


def estimate_token_count(text: str) -> int:
    return max(0, math.ceil(len(text) / 4))


def _safe_raw_metrics(code: str) -> dict[str, int | None]:
    try:
        raw = raw_analyze(code)
    except Exception:
        return {"lloc": None, "sloc": None, "comments": None, "multi": None}
    return {
        "lloc": int(raw.lloc),
        "sloc": int(raw.sloc),
        "comments": int(raw.comments),
        "multi": int(raw.multi),
    }


def _safe_halstead_metrics(code: str) -> dict[str, float | None]:
    try:
        report = h_visit(code).total
    except Exception:
        return {"volume": None, "difficulty": None, "effort": None}
    return {
        "volume": round(float(report.volume), 3),
        "difficulty": round(float(report.difficulty), 3),
        "effort": round(float(report.effort), 3),
    }


def _safe_maintainability_index(code: str) -> float | None:
    try:
        return round(float(mi_visit(code, multi=True)), 3)
    except Exception:
        return None


def _comment_density(raw: dict[str, int | None]) -> float | None:
    sloc = raw.get("sloc")
    comments = raw.get("comments")
    if sloc is None or comments is None:
        return None
    denominator = sloc + comments
    if denominator <= 0:
        return 0.0
    return round(comments / denominator, 6)


def _cc_top_decile_share(complexities: list[int]) -> float | None:
    if len(complexities) < 2:
        return None
    total = sum(complexities)
    if total <= 0:
        return 0.0
    top_n = max(1, math.ceil(len(complexities) * 0.1))
    return round(sum(sorted(complexities, reverse=True)[:top_n]) / total, 6)


def _cc_concentration_note(complexities: list[int]) -> str | None:
    if len(complexities) < 2:
        return "too_few_blocks"
    return None


def _verbosity_ratio(code: str, reference_code: str | None) -> float | None:
    if reference_code is None:
        return None
    denominator = estimate_token_count(reference_code)
    if denominator <= 0:
        return None
    return round(estimate_token_count(code) / denominator, 6)


def _compiled_bloat_ratio(source_code: str, compiled_python: str) -> float | None:
    source_tokens = estimate_token_count(source_code)
    if source_tokens <= 0:
        return None
    return round(estimate_token_count(compiled_python) / source_tokens, 6)


def _redundancy_score(tree: ast.AST) -> float:
    fingerprints: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Load, ast.Store, ast.Del, ast.Module, ast.arguments, ast.arg)):
            continue
        fingerprints.append(ast.dump(node, annotate_fields=False, include_attributes=False))
    if not fingerprints:
        return 0.0
    counts = Counter(fingerprints)
    duplicate_count = sum(count - 1 for count in counts.values() if count > 1)
    return round(duplicate_count / len(fingerprints), 6)


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


def _nonblank_loc(code: str) -> int:
    return len([line for line in code.splitlines() if line.strip()])
