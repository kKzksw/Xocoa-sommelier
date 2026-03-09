"""Runtime wrapper for agentic pre-retrieval orchestration.

This module keeps endpoint logic thin by centralizing:
1) state update + candidate estimation
2) action schema normalization and validation
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from orchestration.agentic_sommelier_engine import (
    agent_step,
    build_agentic_filters,
    build_agentic_retrieval_query,
    normalize_state,
    update_state_from_message,
)


AGENT_ACTION_ASK = "ASK"
AGENT_ACTION_FILTER = "FILTER"
AGENT_ACTION_RETRIEVE = "RETRIEVE"
AGENT_ACTION_VERIFY = "VERIFY"
AGENT_ACTION_FINALIZE = "FINALIZE"

VALID_AGENT_ACTIONS = {
    AGENT_ACTION_ASK,
    AGENT_ACTION_FILTER,
    AGENT_ACTION_RETRIEVE,
    AGENT_ACTION_VERIFY,
    AGENT_ACTION_FINALIZE,
}

VERIFY_MAX_SIMILARITY_MIN = 0.65
VERIFY_SIMILARITY_VARIANCE_MIN = 0.0008
VERIFY_PREFERENCE_COVERAGE_MIN = 0.5
AGENT_TRACE_LIMIT = 30


def normalize_agent_decision(raw: Optional[dict], fallback_state: Optional[dict] = None) -> Dict[str, Any]:
    """Normalize decision payload to a strict internal schema."""
    data = raw if isinstance(raw, dict) else {}
    action = str(data.get("action", AGENT_ACTION_RETRIEVE)).strip().upper()
    if action not in VALID_AGENT_ACTIONS:
        action = AGENT_ACTION_RETRIEVE

    question = str(data.get("question", "")).strip()
    answer_options = [
        str(option).strip()
        for option in data.get("answer_options", []) or []
        if str(option).strip()
    ]
    filters = data.get("filters", {})
    if not isinstance(filters, dict):
        filters = {}

    updated_state = normalize_state(data.get("updated_state", fallback_state or {}))
    fallback_mode = str(data.get("fallback_mode", "")).strip()

    # Guardrail: ask-like actions must include a question.
    if action in {AGENT_ACTION_ASK, AGENT_ACTION_FILTER} and not question:
        action = AGENT_ACTION_RETRIEVE

    return {
        "action": action,
        "question": question,
        "answer_options": answer_options,
        "filters": filters,
        "updated_state": updated_state,
        "fallback_mode": fallback_mode,
    }


def is_question_action(action: str) -> bool:
    normalized = str(action or "").strip().upper()
    return normalized in {AGENT_ACTION_ASK, AGENT_ACTION_FILTER}


def read_agent_trace(state: Optional[dict]) -> List[Dict[str, Any]]:
    normalized = normalize_state(state)
    raw = str(normalized.get("_agent_trace", "") or "").strip()
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, list):
            return []
        cleaned = [entry for entry in parsed if isinstance(entry, dict)]
        return cleaned
    except (TypeError, ValueError, json.JSONDecodeError):
        return []


def _write_agent_trace(state: Optional[dict], trace: List[Dict[str, Any]]) -> Dict[str, str]:
    normalized = normalize_state(state)
    safe_trace = [entry for entry in trace if isinstance(entry, dict)][-AGENT_TRACE_LIMIT:]
    normalized["_agent_trace"] = json.dumps(safe_trace, ensure_ascii=True)
    return normalized


def _append_agent_trace(state: Optional[dict], event: Dict[str, Any]) -> Dict[str, str]:
    trace = read_agent_trace(state)
    trace.append({k: v for k, v in event.items() if v is not None})
    return _write_agent_trace(state, trace)


def run_pre_retrieval_agent_turn(
    user_message: str,
    state: Optional[dict],
    recommender: Any,
    total_catalog_count: int,
) -> Dict[str, Any]:
    """Execute the deterministic pre-retrieval decision phase."""
    conversation_state = normalize_state(state)
    conversation_state = update_state_from_message(user_message, conversation_state)

    filter_bundle = build_agentic_filters(conversation_state)
    probe_query = build_agentic_retrieval_query(
        "",
        conversation_state,
        include_soft_preferences=False,
        include_context=False,
    )
    candidate_count = recommender.estimate_candidate_count(
        probe_query,
        hard_filters=filter_bundle.get("hard"),
    )

    raw_decision = agent_step(
        user_message,
        conversation_state,
        candidate_count,
        total_catalog_count=total_catalog_count,
    )
    decision = normalize_agent_decision(raw_decision, fallback_state=conversation_state)
    updated_state = _append_agent_trace(
        decision.get("updated_state", conversation_state),
        {
            "stage": "pre_retrieval",
            "action": decision.get("action", AGENT_ACTION_RETRIEVE),
            "candidate_count": int(candidate_count),
            "segment": str(conversation_state.get("segment", "")),
        },
    )
    decision["updated_state"] = updated_state

    return {
        "decision": decision,
        "conversation_state": updated_state,
        "candidate_count": int(candidate_count),
        "probe_query": probe_query,
        "filter_bundle": filter_bundle,
    }


def run_retry_agent_turn(
    user_message: str,
    state: Optional[dict],
    candidate_count: int,
    total_catalog_count: int,
) -> Dict[str, Any]:
    """Run a follow-up decision pass after low-confidence retrieval."""
    conversation_state = normalize_state(state)
    raw_decision = agent_step(
        user_message,
        conversation_state,
        candidate_count,
        total_catalog_count=total_catalog_count,
    )
    decision = normalize_agent_decision(raw_decision, fallback_state=conversation_state)
    decision["updated_state"] = _append_agent_trace(
        decision.get("updated_state", conversation_state),
        {
            "stage": "retry",
            "action": decision.get("action", AGENT_ACTION_RETRIEVE),
            "candidate_count": int(candidate_count),
        },
    )
    return decision


def run_post_retrieval_verification(
    user_message: str,
    state: Optional[dict],
    retrieval_result: Optional[dict],
    products: Optional[List[Dict[str, Any]]],
    total_catalog_count: int,
) -> Dict[str, Any]:
    """Verify retrieval quality before final response generation."""
    conversation_state = normalize_state(state)
    result = retrieval_result if isinstance(retrieval_result, dict) else {}
    product_list = products or []
    filters = build_agentic_filters(conversation_state)
    evidence = build_retrieval_evidence(result, product_list)

    max_similarity = float(result.get("max_similarity", 0.0) or 0.0)
    similarity_variance = float(result.get("similarity_variance", 0.0) or 0.0)
    preference_coverage = _compute_preference_coverage(
        explanation_layer=result.get("explanation_layer", {}),
        filters=filters,
    )

    no_products = len(product_list) == 0
    low_similarity = max_similarity < VERIFY_MAX_SIMILARITY_MIN
    low_variance = similarity_variance < VERIFY_SIMILARITY_VARIANCE_MIN
    low_coverage = preference_coverage < VERIFY_PREFERENCE_COVERAGE_MIN

    verify_reason = ""
    if no_products:
        verify_reason = "no_products"
    elif low_similarity:
        verify_reason = "low_similarity"
    elif low_variance:
        verify_reason = "low_variance"
    elif low_coverage:
        verify_reason = "low_preference_coverage"

    if verify_reason:
        retry_decision = run_retry_agent_turn(
            user_message=user_message,
            state=conversation_state,
            candidate_count=max(81, len(result.get("candidates", [])) or 0),
            total_catalog_count=total_catalog_count,
        )
        retry_question = str(retry_decision.get("question", "")).strip()
        retry_options = list(retry_decision.get("answer_options", []))
        if is_question_action(str(retry_decision.get("action", ""))) and retry_question:
            updated_state = _append_agent_trace(
                retry_decision.get("updated_state", conversation_state),
                {
                    "stage": "post_retrieval_verify",
                    "action": AGENT_ACTION_VERIFY,
                    "reason": verify_reason,
                    "max_similarity": max_similarity,
                    "similarity_variance": similarity_variance,
                    "preference_coverage": preference_coverage,
                },
            )
            return {
                "action": AGENT_ACTION_VERIFY,
                "question": retry_question,
                "answer_options": retry_options,
                "updated_state": updated_state,
                "reason": verify_reason,
                "metrics": {
                    "max_similarity": max_similarity,
                    "similarity_variance": similarity_variance,
                    "preference_coverage": preference_coverage,
                },
                "evidence": evidence,
            }

    updated_state = _append_agent_trace(
        conversation_state,
        {
            "stage": "post_retrieval_verify",
            "action": AGENT_ACTION_FINALIZE,
            "reason": "verified",
            "max_similarity": max_similarity,
            "similarity_variance": similarity_variance,
            "preference_coverage": preference_coverage,
        },
    )
    return {
        "action": AGENT_ACTION_FINALIZE,
        "question": "",
        "answer_options": [],
        "updated_state": updated_state,
        "reason": "verified",
        "metrics": {
            "max_similarity": max_similarity,
            "similarity_variance": similarity_variance,
            "preference_coverage": preference_coverage,
        },
        "evidence": evidence,
    }


def build_retrieval_evidence(
    retrieval_result: Optional[dict],
    products: Optional[List[Dict[str, Any]]],
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Create a compact evidence object for top ranked products."""
    result = retrieval_result if isinstance(retrieval_result, dict) else {}
    product_list = products or []

    score_map: Dict[int, float] = {}
    for row in result.get("semantic_scores", []) or []:
        if not isinstance(row, dict):
            continue
        try:
            pid = int(row.get("id"))
            score_map[pid] = float(row.get("score", 0.0) or 0.0)
        except (TypeError, ValueError):
            continue

    evidence: List[Dict[str, Any]] = []
    for product in product_list[:limit]:
        pid_raw = product.get("id")
        try:
            pid = int(pid_raw)
        except (TypeError, ValueError):
            pid = -1

        evidence.append(
            {
                "id": pid_raw,
                "name": product.get("name", ""),
                "brand": product.get("brand", ""),
                "maker_country": product.get("maker_country", ""),
                "origin_country": product.get("origin_country", ""),
                "cocoa_percentage": product.get("cocoa_percentage", ""),
                "similarity_score": float(score_map.get(pid, 0.0)) if pid != -1 else 0.0,
            }
        )

    return evidence


def _compute_preference_coverage(explanation_layer: Optional[dict], filters: Dict[str, Dict[str, Any]]) -> float:
    hard = filters.get("hard", {}) if isinstance(filters, dict) else {}
    soft = filters.get("soft", {}) if isinstance(filters, dict) else {}
    active_fields = set()
    for field, value in {**hard, **soft}.items():
        if field == "origin_scope":
            continue
        if str(value or "").strip():
            active_fields.add(str(field))

    if not active_fields:
        return 1.0

    layer = explanation_layer if isinstance(explanation_layer, dict) else {}
    matched = {
        str(field)
        for field in (layer.get("matched_preferences", []) or [])
        if isinstance(field, str)
    }

    matched_active = matched.intersection(active_fields)
    return len(matched_active) / float(len(active_fields))
