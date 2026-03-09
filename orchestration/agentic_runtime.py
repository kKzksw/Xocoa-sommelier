"""Runtime wrapper for agentic pre-retrieval orchestration.

This module keeps endpoint logic thin by centralizing:
1) state update + candidate estimation
2) action schema normalization and validation
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from orchestration.agentic_sommelier_engine import (
    NON_CONSTRAINT_VALUES,
    SEGMENT_REQUIRED_FIELDS,
    SEGMENT_SELECTION_PROMPT,
    agent_step,
    build_agentic_filters,
    build_agentic_retrieval_query,
    normalize_state,
    update_state_from_message,
)
from orchestration.conversation_policy import (
    describe_candidate_pool,
    generate_sommelier_question,
    select_next_best_attribute,
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
CONVERSATIONAL_POLICY_FIELDS = {
    "chocolate_type",
    "flavor_direction",
    "intensity",
    "cocoa_percentage",
    "origin",
    "budget",
    "brand_preference",
    "context",
}
DISPLAY_SOFT_FIELDS = {
    "flavor_direction",
    "intensity",
    "brand_preference",
    "cocoa_percentage",
}
MIN_CONVERSATIONAL_ASK_TURNS = 3
EARLY_RETRIEVE_DISPLAY_THRESHOLD = 12


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
    updated_state = normalize_state(decision.get("updated_state", conversation_state))
    agent_question = str(decision.get("question", "")).strip()
    agent_target_attr = _agent_asked_attribute(updated_state)
    preserve_agent_question = _should_preserve_agent_question(agent_question, agent_target_attr)
    policy_filters = build_agentic_filters(updated_state)
    candidate_pool = _build_candidate_pool(
        recommender=recommender,
        probe_query=probe_query,
        hard_filters=policy_filters.get("hard", {}),
    )
    display_candidate_count = _estimate_display_candidate_count(
        candidate_pool=candidate_pool,
        state=updated_state,
        recommender=recommender,
    )
    previous_display_count = _as_int(updated_state.get("_last_display_candidate_count", "0"))
    updated_state["_last_display_candidate_count"] = str(display_candidate_count)
    selected_attr = _resolve_selected_attribute(
        candidate_pool=candidate_pool,
        state=updated_state,
        agent_target_attr=agent_target_attr,
    )
    applied_filters = _applied_filter_values(policy_filters, updated_state)
    is_ask_like = is_question_action(str(decision.get("action", "")))
    pool_description = describe_candidate_pool(display_candidate_count, applied_filters)

    if is_ask_like:
        if preserve_agent_question:
            decision["selected_attribute"] = agent_target_attr
        else:
            if (
                previous_display_count > 0
                and display_candidate_count >= previous_display_count
                and selected_attr
            ):
                selected_attr = _next_best_different_attribute(
                    candidate_pool=candidate_pool,
                    state=updated_state,
                    current_attribute=selected_attr,
                ) or selected_attr
            if selected_attr:
                updated_state = _sync_asked_attribute(updated_state, selected_attr)
            question_obj = generate_sommelier_question(
                attribute=selected_attr,
                state=updated_state,
                candidate_count=display_candidate_count,
                applied_filters=applied_filters,
                user_message=user_message,
            )
            decision["question"] = str(question_obj.get("question", "")).strip() or pool_description
            decision["answer_options"] = list(question_obj.get("answer_options", []))
            decision["selected_attribute"] = selected_attr
    elif _should_extend_conversation(
        user_message=user_message,
        decision=decision,
        clarification_turns=_as_int(updated_state.get("_clarification_turns", "0")),
        display_candidate_count=display_candidate_count,
        selected_attr=selected_attr,
    ) or 0 < display_candidate_count <= 40:
        # Optional early recommendation while keeping one refinement question.
        # This avoids "all-or-nothing" completion when the pool is still broad.
        if selected_attr:
            updated_state = _sync_asked_attribute(updated_state, selected_attr, increment_turn=True)
            question_obj = generate_sommelier_question(
                attribute=selected_attr,
                state=updated_state,
                candidate_count=display_candidate_count,
                applied_filters=applied_filters,
                user_message=user_message,
            )
            decision["action"] = AGENT_ACTION_ASK
            decision["question"] = str(question_obj.get("question", "")).strip()
            decision["answer_options"] = list(question_obj.get("answer_options", []))
            decision["selected_attribute"] = selected_attr

    if (
        str(decision.get("action", "")).upper() == AGENT_ACTION_ASK
        and 0 < display_candidate_count <= 40
    ):
        prelim_products, prelim_evidence = _build_preliminary_recommendations(
            recommender=recommender,
            state=updated_state,
            top_k=3,
        )
        if prelim_products:
            prefix = "I already see a few strong matches from what you've shared so far."
            if decision.get("question"):
                decision["question"] = f"{decision['question']}\n\n{prefix}"
            else:
                decision["question"] = f"{pool_description}\n\n{prefix}"
            decision["preliminary_products"] = prelim_products
            decision["preliminary_evidence"] = prelim_evidence

    updated_state = _append_agent_trace(
        updated_state,
        {
            "stage": "pre_retrieval",
            "action": decision.get("action", AGENT_ACTION_RETRIEVE),
            "candidate_count": int(candidate_count),
            "display_candidate_count": int(display_candidate_count),
            "segment": str(updated_state.get("segment", "")),
            "selected_attribute": str(decision.get("selected_attribute", selected_attr or "")),
        },
    )
    decision["updated_state"] = updated_state

    return {
        "decision": decision,
        "conversation_state": updated_state,
        "candidate_count": int(candidate_count),
        "display_candidate_count": int(display_candidate_count),
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


def _agent_asked_attribute(state: Dict[str, str]) -> str:
    raw = str((state or {}).get("_last_asked_field", "") or "").strip()
    if not raw:
        return ""
    return raw


def _should_preserve_agent_question(agent_question: str, agent_target_attr: str) -> bool:
    if (agent_question or "").strip() == SEGMENT_SELECTION_PROMPT.strip():
        return True
    if not agent_target_attr:
        return False
    # Keep deterministic guardrail/safety questions from agent_step unchanged.
    if agent_target_attr not in CONVERSATIONAL_POLICY_FIELDS and agent_target_attr != "broad_narrowing":
        return True
    return False


def _should_extend_conversation(
    user_message: str,
    decision: Dict[str, Any],
    clarification_turns: int,
    display_candidate_count: int,
    selected_attr: str,
) -> bool:
    action = str(decision.get("action", "")).upper()
    if action != AGENT_ACTION_RETRIEVE:
        return False
    if str(decision.get("fallback_mode", "")).strip().upper() == "TASTING_FLIGHT":
        return False
    if not selected_attr:
        return False
    if clarification_turns >= MIN_CONVERSATIONAL_ASK_TURNS:
        return False
    if display_candidate_count <= EARLY_RETRIEVE_DISPLAY_THRESHOLD:
        return False
    if _is_direct_recommendation_message(user_message):
        return False
    return True


def _is_direct_recommendation_message(user_message: str) -> bool:
    text = (user_message or "").strip().lower()
    if not text:
        return False
    patterns = [
        r"\brecommend\b",
        r"\brecommendation\b",
        r"\bshow me\b",
        r"\bgive me\b",
        r"\bbest options?\b",
        r"\bgo ahead\b",
        r"\bjust pick\b",
        r"\b直接推荐\b",
        r"\b推荐\b",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def _resolve_selected_attribute(
    candidate_pool: List[Dict],
    state: Dict[str, str],
    agent_target_attr: str,
) -> str:
    segment = str((state or {}).get("segment", "") or "")
    required_fields = set(SEGMENT_REQUIRED_FIELDS.get(segment, []))
    if agent_target_attr in required_fields:
        return agent_target_attr
    if agent_target_attr in {"segment", "origin_scope"}:
        return agent_target_attr
    if agent_target_attr in CONVERSATIONAL_POLICY_FIELDS:
        preferred = select_next_best_attribute(candidate_pool, state)
        return preferred or agent_target_attr
    # "broad_narrowing" is a meta prompt; translate it into one concrete
    # high-impact attribute to preserve one-question-per-turn behavior.
    return select_next_best_attribute(candidate_pool, state)


def _next_best_different_attribute(
    candidate_pool: List[Dict],
    state: Dict[str, str],
    current_attribute: str,
) -> str:
    shadow = normalize_state(state)
    asked = _asked_fields(shadow)
    asked.add(current_attribute)
    shadow["_asked_fields"] = ",".join(sorted(asked))
    candidate = select_next_best_attribute(candidate_pool, shadow)
    return candidate if candidate and candidate != current_attribute else ""


def _estimate_display_candidate_count(
    candidate_pool: List[Dict],
    state: Dict[str, str],
    recommender: Any,
) -> int:
    if not candidate_pool:
        return 0

    soft_constraints = _active_display_constraints(state)
    if not soft_constraints:
        return len(candidate_pool)

    estimated = 0.0
    for product in candidate_pool:
        weight = 1.0
        for field, value in soft_constraints.items():
            status = _soft_field_status(
                recommender=recommender,
                field=field,
                value=value,
                state=state,
                product=product,
            )
            factor = 1.0 if status == "match" else 0.35 if status == "unknown" else 0.0
            weight *= factor
            if weight <= 0.0:
                break
        estimated += weight

    narrowed = int(round(estimated))
    if narrowed <= 0:
        return 1
    return max(1, min(len(candidate_pool), narrowed))


def _active_display_constraints(state: Dict[str, str]) -> Dict[str, str]:
    constraints: Dict[str, str] = {}
    for field in DISPLAY_SOFT_FIELDS:
        value = str((state or {}).get(field, "") or "").strip()
        if _is_effective_value(value):
            constraints[field] = value
    return constraints


def _is_effective_value(value: str) -> bool:
    text = str(value or "").strip().lower()
    if not text:
        return False
    if text in NON_CONSTRAINT_VALUES:
        return False
    return text not in {"not required"}


def _soft_field_status(
    recommender: Any,
    field: str,
    value: str,
    state: Dict[str, str],
    product: Dict[str, Any],
) -> str:
    if field == "context":
        # Gift/everyday is mostly a rerank hint, not a hard discriminator.
        return "unknown"

    if field == "cocoa_percentage":
        target = _first_number(value)
        cocoa = _first_number(str(product.get("cocoa_percentage", "")))
        if target is None or cocoa is None:
            return "unknown"
        return "match" if abs(target - cocoa) <= 8.0 else "mismatch"

    field_status = getattr(recommender, "_field_status", None)
    if callable(field_status):
        try:
            status = field_status(
                field,
                product,
                str(value).strip().lower(),
                origin_scope=str((state or {}).get("origin_scope", "") or "").strip().lower(),
            )
            if status in {"match", "mismatch", "unknown"}:
                return status
        except Exception:
            pass

    if field == "flavor_direction":
        blob = " ".join(
            [
                str(product.get("flavor_notes_primary", "")),
                str(product.get("flavor_notes_secondary", "")),
                str(product.get("tasting_notes", "")),
                str(product.get("name", "")),
            ]
        ).lower()
        if not blob.strip():
            return "unknown"
        tokens = [token.strip().lower() for token in str(value).split(",") if token.strip()]
        return "match" if any(token in blob for token in tokens) else "unknown"

    if field == "intensity":
        cocoa = _first_number(str(product.get("cocoa_percentage", "")))
        if cocoa is None:
            return "unknown"
        preference = str(value).strip().lower()
        if preference == "intense":
            return "match" if cocoa >= 75.0 else "mismatch"
        if preference == "smooth":
            return "match" if cocoa <= 65.0 else "mismatch"
        return "unknown"

    return "unknown"


def _first_number(value: str) -> Optional[float]:
    match = re.search(r"(\d+(?:\.\d+)?)", str(value or ""))
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _build_candidate_pool(
    recommender: Any,
    probe_query: str,
    hard_filters: Dict[str, str],
) -> List[Dict]:
    try:
        candidate_ids = recommender.channel_a.run(probe_query)
    except Exception:
        return []

    ids = candidate_ids
    apply_filter = getattr(recommender, "_apply_dynamic_hard_filters", None)
    if callable(apply_filter):
        try:
            filtered_ids, _, _ = apply_filter(candidate_ids, hard_filters)
            ids = filtered_ids
        except Exception:
            ids = candidate_ids

    pool = []
    by_id = getattr(recommender, "product_by_id", {})
    for pid in ids:
        product = by_id.get(int(pid))
        if isinstance(product, dict):
            pool.append(product)
    return pool


def _applied_filter_values(
    filters: Dict[str, Dict[str, str]],
    state: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    applied: Dict[str, str] = {}
    hard = filters.get("hard", {}) if isinstance(filters, dict) else {}
    soft = filters.get("soft", {}) if isinstance(filters, dict) else {}
    for field, value in {**hard, **soft}.items():
        if field == "origin_scope":
            continue
        text = str(value or "").strip()
        if text:
            applied[field] = text
    context = str((state or {}).get("context", "") or "").strip()
    if context:
        applied["context"] = context
    return applied


def _sync_asked_attribute(
    state: Dict[str, str],
    attribute: str,
    increment_turn: bool = False,
) -> Dict[str, str]:
    updated = normalize_state(state)
    asked = _asked_fields(updated)
    asked.add(attribute)
    updated["_asked_fields"] = ",".join(sorted(asked))
    updated["_last_asked_field"] = attribute
    if increment_turn:
        updated["_clarification_turns"] = str(_as_int(updated.get("_clarification_turns", "0")) + 1)
    return updated


def _asked_fields(state: Dict[str, str]) -> set[str]:
    raw = str(state.get("_asked_fields", "") or "").strip()
    if not raw:
        return set()
    return {token.strip() for token in raw.split(",") if token.strip()}


def _as_int(value: str) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _build_preliminary_recommendations(
    recommender: Any,
    state: Dict[str, str],
    top_k: int = 3,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    try:
        query = build_agentic_retrieval_query("", state)
        filters = build_agentic_filters(state)
        result = recommender.recommend(
            query=query,
            top_k=max(2, int(top_k)),
            segment=state.get("segment"),
            state=state,
            hard_filters=filters.get("hard", {}),
        )
        ranked_ids = list(result.get("ranked", []) or [])
        by_id = getattr(recommender, "product_by_id", {})
        products = [by_id.get(int(pid)) for pid in ranked_ids[:top_k] if isinstance(by_id.get(int(pid)), dict)]
        evidence = build_retrieval_evidence(result, products, limit=top_k)
        return products, evidence
    except Exception:
        return [], []
