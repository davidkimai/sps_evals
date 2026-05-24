from __future__ import annotations

import json
import time
from dataclasses import asdict
from typing import Any

from openai import OpenAI

from specoracle.vericoding.runtime_env import estimate_openai_cost, extract_usage
from specoracle.vericoding.schemas import (
    ObservableCandidateView,
    SELECTOR_PROMPT_VERSION,
    stable_hash,
)
from specoracle.vericoding.selection_features import candidate_feature_score

FORBIDDEN_SELECTOR_FIELDS = {
    "candidate_label",
    "hidden_tests_pass",
    "property_checks_pass",
    "security_checks_pass",
    "regression_checks_pass",
    "deceptive_candidate",
    "insecure_candidate",
    "regression_candidate",
    "candidate_source_type",
    "candidate_source",
    "generator_condition",
    "candidate_lineage",
    "candidate_condition_id",
    "generation_mode",
    "oracle_family",
    "pool_regime",
}


class SelectorDecisionError(ValueError):
    """Raised when a claim-bearing provider selector does not emit usable JSON."""


def observable_views(candidate_rows: list[dict[str, Any]]) -> list[ObservableCandidateView]:
    return [ObservableCandidateView.from_candidate_row(row) for row in candidate_rows]


def select_tests_only_observable(views: list[ObservableCandidateView]) -> ObservableCandidateView:
    return sorted(
        views,
        key=lambda view: (
            not view.visible_tests_pass,
            not view.visible_compile_pass,
            view.candidate_id,
        ),
    )[0]


def select_structural_observable(views: list[ObservableCandidateView]) -> ObservableCandidateView:
    return sorted(
        views,
        key=lambda view: (
            view.cc_average if view.cc_average is not None else 999.0,
            view.max_nesting_depth if view.max_nesting_depth is not None else 999,
            -(view.maintainability_index if view.maintainability_index is not None else 0.0),
            view.candidate_id,
        ),
    )[0]


def select_random_observable(views: list[ObservableCandidateView], *, task_id: str) -> ObservableCandidateView:
    return sorted(views, key=lambda view: stable_hash({"task_id": task_id, "id": view.candidate_id}))[0]


def select_llm_judge_live(
    views: list[ObservableCandidateView],
    *,
    task_summary: str,
    model: str,
    claim_bearing: bool = False,
) -> tuple[ObservableCandidateView | None, dict[str, Any]]:
    shortlist = _shortlist(views)
    return _provider_tournament(
        shortlist,
        task_summary=task_summary,
        model=model,
        selector_name="llm_judge_selector",
        claim_bearing=claim_bearing,
        instructions=(
            "You are judging candidate code using only visible evidence. "
            "Prefer candidates that visibly compile, pass visible tests, and have simpler structure."
        ),
    )


def select_specoracle_live(
    views: list[ObservableCandidateView],
    *,
    task_summary: str,
    model: str,
    claim_bearing: bool = False,
) -> tuple[ObservableCandidateView | None, dict[str, Any]]:
    shortlist = _shortlist(views)
    return _provider_tournament(
        shortlist,
        task_summary=task_summary,
        model=model,
        selector_name="specoracle_selector",
        claim_bearing=claim_bearing,
        instructions=(
            "You are a SpecOracle selector. Use the lightweight spec and visible evidence "
            "as a ranking oracle. Reject visibly catastrophic, over-complex, or underspecified "
            "candidates. Never assume hidden tests."
        ),
    )


def _shortlist(views: list[ObservableCandidateView], k: int = 4) -> list[ObservableCandidateView]:
    return sorted(
        views,
        key=lambda view: (
            -candidate_feature_score(view.to_selector_dict()),
            view.candidate_id,
        ),
    )[:k]


def _provider_tournament(
    views: list[ObservableCandidateView],
    *,
    task_summary: str,
    model: str,
    selector_name: str,
    claim_bearing: bool,
    instructions: str,
) -> tuple[ObservableCandidateView | None, dict[str, Any]]:
    start = time.monotonic()
    handle_by_id = {view.candidate_id: f"candidate_{idx + 1}" for idx, view in enumerate(views)}
    id_by_handle = {handle: candidate_id for candidate_id, handle in handle_by_id.items()}
    candidate_payload = [
        view.to_claim_bearing_selector_dict(candidate_handle=handle_by_id[view.candidate_id])
        if claim_bearing
        else asdict(view)
        for view in views
    ]
    output_id_name = "candidate_handle" if claim_bearing else "candidate_id"
    chosen_field_name = "chosen_candidate" if claim_bearing else "chosen_candidate_id"
    payload = {
        "task_summary": task_summary,
        "candidates": candidate_payload,
        "output_schema": {
            "compared_candidates": [output_id_name],
            chosen_field_name: output_id_name,
            "confidence": 0.0,
            "rationale_tags": ["visible evidence tag"],
            "failure_tags": ["visible failure tag"],
            "visible_evidence_considered": ["visible field"],
        },
    }
    client = OpenAI(timeout=45.0)
    attempts = 2 if claim_bearing else 1
    response = None
    text = ""
    decision: dict[str, Any] | None = None
    provider_failed = False
    provider_error_class = ""
    for attempt in range(attempts):
        for provider_attempt in range(3):
            try:
                response = client.responses.create(
                    model=model,
                    instructions=(
                        f"{instructions}\nReturn strict JSON only. Do not use hidden labels, hidden tests, "
                        "security outcomes, regression outcomes, source labels, generator conditions, or any "
                        "field not present in the candidate list."
                    ),
                    input=json.dumps(payload, sort_keys=True),
                    max_output_tokens=700,
                )
                break
            except Exception as exc:
                provider_error_class = exc.__class__.__name__
                if provider_attempt == 2:
                    provider_failed = True
                    break
                time.sleep(2.0 * (provider_attempt + 1))
        if provider_failed:
            decision = None
            break
        text = _response_text(response)
        try:
            decision = _parse_decision(
                text,
                list(id_by_handle if claim_bearing else [view.candidate_id for view in views]),
                allow_default=not claim_bearing,
                chosen_key="chosen_candidate" if claim_bearing else "chosen_candidate_id",
            )
            break
        except SelectorDecisionError:
            if attempt + 1 >= attempts:
                decision = None
    usage = extract_usage(response) if response is not None else {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0}
    chosen = None
    if decision is not None:
        chosen_id = id_by_handle.get(decision["chosen_candidate_id"], decision["chosen_candidate_id"])
        chosen = next((view for view in views if view.candidate_id == chosen_id), None)
    meta = {
        "selector_name": selector_name,
        "selector_prompt_version": SELECTOR_PROMPT_VERSION,
        "selector_prompt_hash": stable_hash(payload),
        "selector_view": "anonymized_claim_bearing" if claim_bearing else "legacy_observable",
        "provider": "openai",
        "model": model,
        "selector_cost_usd": estimate_openai_cost(
            model,
            usage["input_tokens"],
            usage["output_tokens"],
            cached_input_tokens=usage["cached_input_tokens"],
        ),
        "selector_input_tokens": usage["input_tokens"],
        "selector_cached_input_tokens": usage["cached_input_tokens"],
        "selector_output_tokens": usage["output_tokens"],
        "selector_wall_seconds": round(time.monotonic() - start, 3),
        "comparison_count": max(0, len(views) - 1),
        "decision": decision,
        "selector_parse_failed": decision is None or chosen is None,
        "selector_provider_failed": provider_failed,
        "selector_provider_error_class": provider_error_class,
        "live_call_id": str(getattr(response, "id", "")) if response is not None else "",
    }
    return chosen, meta


def _response_text(response: Any) -> str:
    text = getattr(response, "output_text", None)
    if text:
        return str(text)
    if hasattr(response, "model_dump"):
        payload = response.model_dump()
        chunks: list[str] = []
        for item in payload.get("output", []):
            for content in item.get("content", []):
                if content.get("text"):
                    chunks.append(str(content["text"]))
        return "\n".join(chunks)
    return str(response)


def _parse_decision(
    text: str,
    candidate_ids: list[str],
    *,
    allow_default: bool = True,
    chosen_key: str = "chosen_candidate_id",
) -> dict[str, Any]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        if not allow_default:
            raise SelectorDecisionError("selector response was not valid JSON")
        payload = {}
    chosen = str(payload.get(chosen_key) or payload.get("chosen_candidate_id") or "")
    if chosen not in set(candidate_ids):
        if not allow_default:
            raise SelectorDecisionError("selector response did not choose a valid candidate")
        chosen = candidate_ids[0]
    return {
        "compared_candidate_ids": candidate_ids,
        "chosen_candidate_id": chosen,
        "confidence": float(payload.get("confidence") or 0.5),
        "rationale_tags": list(payload.get("rationale_tags") or ["fallback_parse"]),
        "failure_tags": list(payload.get("failure_tags") or []),
        "visible_evidence_considered": list(
            payload.get("visible_evidence_considered") or ["visible_compile_pass", "visible_tests_pass"]
        ),
        "raw_parse_ok": bool(payload),
    }
