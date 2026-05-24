from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from specoracle.vericoding.schemas import now_iso, stable_hash

REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCED_SHELL_PREFIX = "source ~/.zshrc >/dev/null 2>&1; "
OPENAI_TEXT_PRICE_PER_MILLION = {
    "gpt-5.4-mini": {"input": 0.75, "cached_input": 0.075, "output": 4.50},
    "gpt-5.4-nano": {"input": 0.20, "cached_input": 0.02, "output": 1.25},
    "gpt-5.4": {"input": 2.50, "cached_input": 0.25, "output": 15.00},
    "gpt-5.5": {"input": 5.00, "cached_input": 0.50, "output": 30.00},
    "gpt-5.4-pro": {"input": 30.00, "cached_input": 0.0, "output": 180.00},
    "gpt-5.5-pro": {"input": 30.00, "cached_input": 0.0, "output": 180.00},
}


@dataclass(frozen=True)
class RuntimeProvenance:
    runner_git_commit: str
    runner_git_dirty: bool
    diff_fingerprint: str
    dirty_override: bool
    child_env_verified: bool
    sanctioned_dirty_run_root: bool = False
    sanctioned_dirty_paths: tuple[str, ...] = ()
    run_root: str = ""

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def run_sourced_shell(command: str, *, timeout_seconds: float | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["zsh", "-lc", SOURCED_SHELL_PREFIX + command],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )


def load_sourced_env() -> dict[str, str]:
    completed = run_sourced_shell(
        "python3 - <<'PY'\n"
        "import json, os\n"
        "keys=['OPENAI_API_KEY','ANTHROPIC_API_KEY','GOOGLE_API_KEY']\n"
        "print(json.dumps({k: bool(os.getenv(k)) for k in keys}, sort_keys=True))\n"
        "PY",
        timeout_seconds=30,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "failed to load sourced environment")
    flags = json.loads(completed.stdout.strip() or "{}")
    env = os.environ.copy()
    if not flags.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not visible after sourcing ~/.zshrc")
    env["SPECORACLE_SOURCED_ENV_VERIFIED"] = "1"
    return env


def verify_child_env_path() -> bool:
    completed = run_sourced_shell(
        "python3 - <<'PY'\n"
        "import os\n"
        "raise SystemExit(0 if os.getenv('OPENAI_API_KEY') else 7)\n"
        "PY",
        timeout_seconds=30,
    )
    return completed.returncode == 0


def provider_minimal_request(model: str = "gpt-5.4-mini") -> dict[str, Any]:
    start = time.monotonic()
    from openai import OpenAI

    client = OpenAI()
    response = client.responses.create(
        model=model,
        instructions="Return strict JSON only.",
        input='Return {"ok": true}.',
        max_output_tokens=32,
    )
    usage = extract_usage(response)
    return {
        "provider": "openai",
        "model": model,
        "ok": True,
        "input_tokens": usage["input_tokens"],
        "cached_input_tokens": usage["cached_input_tokens"],
        "output_tokens": usage["output_tokens"],
        "cost_usd": estimate_openai_cost(
            model,
            usage["input_tokens"],
            usage["output_tokens"],
            cached_input_tokens=usage["cached_input_tokens"],
        ),
        "wall_seconds": round(time.monotonic() - start, 3),
        "response_id": str(getattr(response, "id", "")),
    }


def extract_usage(response: Any) -> dict[str, int]:
    usage = getattr(response, "usage", None)
    input_tokens = int(getattr(usage, "input_tokens", 0) or getattr(usage, "prompt_tokens", 0) or 0)
    output_tokens = int(
        getattr(usage, "output_tokens", 0) or getattr(usage, "completion_tokens", 0) or 0
    )
    cached_input_tokens = _cached_tokens_from_usage(usage)
    if not input_tokens and hasattr(response, "model_dump"):
        payload = response.model_dump()
        usage_payload = payload.get("usage") or {}
        input_tokens = int(usage_payload.get("input_tokens") or usage_payload.get("prompt_tokens") or 0)
        output_tokens = int(
            usage_payload.get("output_tokens") or usage_payload.get("completion_tokens") or 0
        )
        cached_input_tokens = _cached_tokens_from_payload(usage_payload)
    return {
        "input_tokens": input_tokens,
        "cached_input_tokens": min(cached_input_tokens, input_tokens),
        "output_tokens": output_tokens,
    }


def estimate_openai_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    *,
    cached_input_tokens: int = 0,
) -> float:
    prices = _price_for_model(model)
    cached_tokens = max(0, min(int(cached_input_tokens or 0), int(input_tokens or 0)))
    uncached_tokens = max(0, int(input_tokens or 0) - cached_tokens)
    input_cost = uncached_tokens * prices["input"] / 1_000_000
    cached_cost = cached_tokens * prices["cached_input"] / 1_000_000
    output_cost = max(0, int(output_tokens or 0)) * prices["output"] / 1_000_000
    return round(max(0.000001, input_cost + cached_cost + output_cost), 6)


def _price_for_model(model: str) -> dict[str, float]:
    normalized = model.lower()
    if normalized in OPENAI_TEXT_PRICE_PER_MILLION:
        return OPENAI_TEXT_PRICE_PER_MILLION[normalized]
    for key in sorted(OPENAI_TEXT_PRICE_PER_MILLION, key=len, reverse=True):
        if key in normalized:
            return OPENAI_TEXT_PRICE_PER_MILLION[key]
    return OPENAI_TEXT_PRICE_PER_MILLION["gpt-5.4-mini"]


def _cached_tokens_from_usage(usage: Any) -> int:
    if usage is None:
        return 0
    details = getattr(usage, "input_tokens_details", None) or getattr(usage, "prompt_tokens_details", None)
    if isinstance(details, dict):
        return int(details.get("cached_tokens") or details.get("cached_input_tokens") or 0)
    return int(getattr(details, "cached_tokens", 0) or getattr(details, "cached_input_tokens", 0) or 0)


def _cached_tokens_from_payload(usage_payload: dict[str, Any]) -> int:
    details = usage_payload.get("input_tokens_details") or usage_payload.get("prompt_tokens_details") or {}
    return int(details.get("cached_tokens") or details.get("cached_input_tokens") or 0)


def git_provenance(*, dirty_override: bool = False) -> RuntimeProvenance:
    commit = _git("rev-parse", "--short", "HEAD") or "unknown"
    status = _git("status", "--short")
    diff = _git("diff", "--binary") + "\n" + _git("diff", "--cached", "--binary")
    untracked = _git("ls-files", "--others", "--exclude-standard")
    fingerprint = hashlib.sha256((diff + "\nUNTRACKED\n" + untracked).encode("utf-8")).hexdigest()
    return RuntimeProvenance(
        runner_git_commit=commit,
        runner_git_dirty=bool(status),
        diff_fingerprint=fingerprint,
        dirty_override=dirty_override,
        child_env_verified=verify_child_env_path(),
    )


def assert_clean_or_override(*, allow_dirty_live: bool) -> RuntimeProvenance:
    provenance = git_provenance(dirty_override=allow_dirty_live)
    if provenance.runner_git_dirty and not allow_dirty_live:
        raise RuntimeError(
            "run-all-live requires a clean committed tree; rerun with --allow-dirty-live "
            "only if the dirty provenance is intentionally part of the live evidence."
        )
    return provenance


def assert_clean_or_sanctioned_run_root(
    *,
    run_root: Path,
    allow_dirty_live: bool,
    state: dict[str, Any],
    resume: bool,
) -> RuntimeProvenance:
    provenance = git_provenance(dirty_override=allow_dirty_live)
    if not provenance.runner_git_dirty or allow_dirty_live:
        return provenance
    dirty_paths = git_dirty_paths()
    if not dirty_paths_confined_to_root(dirty_paths, run_root):
        outside = [path for path in dirty_paths if not path_under_root(path, run_root)]
        raise RuntimeError(
            "dirty live execution blocked because non-run-root paths are dirty: "
            + ", ".join(outside[:8])
        )
    if _has_clean_launch(state) or (not resume and _has_clean_preflight(state)):
        return RuntimeProvenance(
            runner_git_commit=provenance.runner_git_commit,
            runner_git_dirty=provenance.runner_git_dirty,
            diff_fingerprint=provenance.diff_fingerprint,
            dirty_override=False,
            child_env_verified=provenance.child_env_verified,
            sanctioned_dirty_run_root=True,
            sanctioned_dirty_paths=tuple(dirty_paths),
            run_root=_run_root_rel(run_root),
        )
    raise RuntimeError(
        "dirty live execution blocked because the tree is dirty and no clean launch "
        "or clean preflight provenance exists for this run root"
    )


def git_dirty_paths() -> list[str]:
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0 or not completed.stdout:
        return []
    entries = [entry for entry in completed.stdout.split("\0") if entry]
    paths: list[str] = []
    index = 0
    while index < len(entries):
        entry = entries[index]
        status = entry[:2]
        path = entry[3:]
        paths.append(path)
        if status[0] in {"R", "C"} and index + 1 < len(entries):
            index += 2
        else:
            index += 1
    return sorted(set(paths))


def dirty_paths_confined_to_root(paths: list[str], run_root: Path) -> bool:
    return all(path_under_root(path, run_root) for path in paths)


def path_under_root(path: str, run_root: Path) -> bool:
    root = _run_root_rel(run_root)
    candidate = path.rstrip("/")
    prefix = root.rstrip("/") + "/"
    return candidate == root.rstrip("/") or candidate.startswith(prefix)


def harbor_available() -> bool:
    return bool(harbor_probe()["available"])


def harbor_probe() -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["uvx", "--from", "harbor==0.7.0", "harbor", "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"available": False, "error": "harbor_help_timeout_120s"}
    return {
        "available": completed.returncode == 0,
        "error": "" if completed.returncode == 0 else (completed.stderr or completed.stdout or "").strip()[:500],
    }


def inspect_import_available() -> bool:
    completed = subprocess.run(
        ["python3", "-c", "import inspect_ai; import slopbench_inspect"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return completed.returncode == 0


def preflight_report(*, model: str, allow_dirty_live: bool) -> dict[str, Any]:
    provenance = git_provenance(dirty_override=allow_dirty_live)
    provider = provider_minimal_request(model=model)
    harbor = harbor_probe()
    return {
        "schema_version": "vericoding_depth_v2_preflight_v1",
        "created_at": now_iso(),
        **provenance.to_dict(),
        "openai_api_key_present": bool(os.getenv("OPENAI_API_KEY")),
        "provider_minimal_request": provider,
        "harbor_available": harbor["available"],
        "harbor_probe_error": harbor["error"],
        "inspect_import_available": inspect_import_available(),
        "hidden_oracle_dir_ignored": _is_ignored("artifacts/vericoding_depth_v2_hidden_oracles"),
        "child_env_path": "verified_in_sourced_shell" if provenance.child_env_verified else "unverified",
        "preflight_hash": stable_hash(
            {
                "commit": provenance.runner_git_commit,
                "diff": provenance.diff_fingerprint,
                "provider": provider.get("response_id"),
            }
        ),
    }


def _is_ignored(path: str) -> bool:
    completed = subprocess.run(
        ["git", "check-ignore", "-q", path],
        cwd=REPO_ROOT,
        check=False,
    )
    return completed.returncode == 0


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _run_root_rel(run_root: Path) -> str:
    root = run_root if run_root.is_absolute() else REPO_ROOT / run_root
    try:
        return root.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return run_root.as_posix().rstrip("/")


def _has_clean_launch(state: dict[str, Any]) -> bool:
    return bool(state.get("clean_launch")) and not bool(state.get("launch_dirty_override"))


def _has_clean_preflight(state: dict[str, Any]) -> bool:
    preflight = state.get("preflight") or {}
    return bool(preflight) and not bool(preflight.get("runner_git_dirty")) and not bool(
        preflight.get("dirty_override")
    )
