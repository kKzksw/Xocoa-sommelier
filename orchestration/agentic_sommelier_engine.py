"""Agentic clarification and narrowing flow before retrieval.

This module is intentionally deterministic for filtering and state transitions.
LLM support is optional and only used for structured ambiguity checks.
"""

from __future__ import annotations

import os
import re
from typing import Callable, Dict, List, Optional, Set

SEGMENT_SELECTION_PROMPT = (
    "When choosing chocolate, what matters most to you?\n"
    "A) Taste & flavor experience\n"
    "B) Health & ethical sourcing\n"
    "C) Good value & familiar brands"
)

SEGMENT_MAP = {
    "A": "Impulsive-Involved",
    "B": "Rational Health-Conscious",
    "C": "Uninvolved",
}

STATE_FIELDS = [
    "segment",
    "context",
    "origin",
    "origin_scope",
    "chocolate_type",
    "flavor_direction",
    "intensity",
    "budget",
    "certification",
    "dietary",
    "cocoa_percentage",
    "brand_preference",
]

# Internal fields are persisted in conversation state to enforce max-question policy.
INTERNAL_FIELDS = [
    "_clarification_turns",
    "_ambiguous_turns",
    "_asked_fields",
    "_last_asked_field",
    "_shown_product_ids",
    "_explicit_hard_fields",
    "_agent_trace",
]

SEGMENT_REQUIRED_FIELDS = {
    "Impulsive-Involved": ["chocolate_type"],
    "Rational Health-Conscious": ["certification"],
    "Uninvolved": ["budget"],
}

SEGMENT_OPTIONAL_FIELDS = {
    "Impulsive-Involved": ["flavor_direction", "intensity", "context"],
    "Rational Health-Conscious": ["dietary", "cocoa_percentage", "context"],
    "Uninvolved": ["brand_preference", "context"],
}

QUESTION_TEXT = {
    "Impulsive-Involved": {
        "chocolate_type": "Do you prefer milk, dark, or white chocolate?",
        "flavor_direction": (
            "What flavor direction do you prefer? Sweet / Dark / Fruity / Nutty / Caramel / Spicy?"
        ),
        "intensity": "Do you enjoy intense chocolate or something smoother and creamy?",
        "context": "Is this for a romantic gift, a celebration, or a casual treat?",
    },
    "Rational Health-Conscious": {
        "certification": (
            "Are certifications important to you (organic, fair trade, sustainability)?"
        ),
        "dietary": "Do you have any dietary preferences (vegan, low sugar, dairy-free, etc.)?",
        "cocoa_percentage": "Are you looking for a specific cocoa percentage or intensity?",
        "context": "Since this may be a gift, should eco-friendly packaging also be prioritized?",
    },
    "Uninvolved": {
        "budget": "What budget range are you considering?",
        "brand_preference": (
            "Do you prefer familiar brands or are you open to discovering something new?"
        ),
        "context": "Is this for everyday enjoyment or a gift?",
    },
}

ORIGIN_SCOPE_QUESTION = (
    "When you say chocolate from a country, which one do you mean?\n"
    "1) Made by brands/manufacturers in that country\n"
    "2) Cocoa bean origin from that country"
)

CANDIDATE_RETRIEVE_THRESHOLD = 80
MAX_CLARIFICATION_QUESTIONS = 5
MIN_DYNAMIC_RETRIEVE_THRESHOLD = 5
CATALOG_RETRIEVE_RATIO = 0.25
EARLY_DIRECT_RETRIEVE_THRESHOLD = 8
BROAD_NARROWING_MIN_CANDIDATES = 120

# Constraint priorities:
# 1) Explicit constraints from user messages
# 2) Hard constraints (inferred / persisted)
# 3) Segment required fields
# 4) Soft preferences
HARD_CONSTRAINT_FIELDS = [
    "origin",
    "origin_scope",
    "chocolate_type",
    "budget",
    "dietary",
    "certification",
]

SOFT_PREFERENCE_FIELDS = [
    "flavor_direction",
    "intensity",
    "brand_preference",
]

ANSWER_OPTIONS_BY_FIELD = {
    "budget": ["Under $10", "$10-$20", "$20-$40", "Premium (>$40)", "No budget limit"],
    "chocolate_type": ["Milk", "Dark", "White", "No preference"],
    "flavor_direction": ["Sweet", "Dark", "Fruity", "Nutty", "Caramel", "Spicy", "No preference"],
    "intensity": ["Intense / Bold", "Smooth / Creamy", "No preference"],
    "context": ["Romantic gift", "Celebration", "Casual treat"],
}

NON_CONSTRAINT_VALUES = {
    "no preference",
    "any",
    "whatever",
    "not sure",
    "doesn't matter",
    "doesnt matter",
}

AMBIGUOUS_ANY_PATTERNS = [
    r"\bany\b",
    r"\banything\b",
    r"\bwhatever\b",
    r"\bno preference\b",
    r"\bup to you\b",
    r"\bsurprise me\b",
]

_AMBIGUITY_HELPER: Optional[
    Callable[[str, Dict[str, str], List[str]], Dict[str, object]]
] = None


def _segment_mode() -> str:
    mode = (os.getenv("SEGMENT_MODE", "free_text") or "").strip().lower()
    if mode in {"clickbox", "click_box", "click-box"}:
        return "clickbox"
    return "free_text"


def set_ambiguity_helper(
    helper: Optional[Callable[[str, Dict[str, str], List[str]], Dict[str, object]]]
) -> None:
    """Register optional LLM helper returning JSON:

    {
      "needs_more_info": bool,
      "missing_fields": list[str]
    }
    """
    global _AMBIGUITY_HELPER
    _AMBIGUITY_HELPER = helper


def default_state() -> Dict[str, str]:
    state = {field: "" for field in STATE_FIELDS}
    for field in INTERNAL_FIELDS:
        state[field] = ""
    return state


def normalize_state(state: Optional[dict]) -> Dict[str, str]:
    normalized = default_state()
    if not isinstance(state, dict):
        return normalized

    for key, value in state.items():
        if key in normalized:
            normalized[key] = "" if value is None else str(value).strip()

    # Keep backward compatibility with previous state naming.
    legacy_taste = "" if state.get("taste") is None else str(state.get("taste", "")).strip()
    if legacy_taste and not normalized["flavor_direction"]:
        normalized["flavor_direction"] = legacy_taste

    return normalized


def detect_segment_from_clickbox(user_message: str) -> Optional[str]:
    text = (user_message or "").strip().lower()
    if not text:
        return None

    letter_match = re.fullmatch(r"(?:option\s*)?([abc])[\)\.:]?", text)
    if letter_match:
        return SEGMENT_MAP.get(letter_match.group(1).upper())

    if "taste" in text or "flavor experience" in text:
        return "Impulsive-Involved"
    if "health" in text or "ethical sourcing" in text:
        return "Rational Health-Conscious"
    if "good value" in text or "familiar brands" in text:
        return "Uninvolved"

    return None


def update_state_from_message(user_message: str, state: Optional[dict]) -> Dict[str, str]:
    merged = normalize_state(state)
    text = (user_message or "").strip()
    lower = text.lower()
    relax_targets = _extract_relax_targets(lower)
    if relax_targets:
        merged = _apply_relaxation(merged, relax_targets)

    segment = detect_segment_from_clickbox(text)
    if segment:
        merged["segment"] = segment

    if _has_gift_context(lower):
        merged["context"] = "gift"
    elif any(token in lower for token in ["everyday", "daily", "casual"]):
        merged["context"] = "everyday"

    origin = _extract_origin(lower)
    if origin and origin.lower() not in {"that country", "this country"}:
        merged["origin"] = origin

    origin_scope = _extract_origin_scope(lower)
    if origin_scope:
        merged["origin_scope"] = origin_scope

    choc_type = _extract_chocolate_type(lower)
    if choc_type:
        merged["chocolate_type"] = choc_type

    flavor = _extract_flavor_direction(lower)
    if flavor:
        merged["flavor_direction"] = flavor

    intensity = _extract_intensity(lower)
    if intensity:
        merged["intensity"] = intensity

    budget = "" if "budget" in relax_targets else _extract_budget(lower)
    if budget:
        merged["budget"] = budget

    certification = (
        ""
        if "certification" in relax_targets
        else _extract_certification(
            lower,
            merged.get("segment", ""),
            merged.get("_last_asked_field", ""),
        )
    )
    if certification:
        merged["certification"] = certification

    dietary = "" if "dietary" in relax_targets else _extract_dietary(lower)
    if dietary:
        merged["dietary"] = dietary

    cocoa = "" if "cocoa_percentage" in relax_targets else _extract_cocoa_percentage(lower)
    if cocoa:
        merged["cocoa_percentage"] = cocoa

    brand_pref = "" if "brand_preference" in relax_targets else _extract_brand_preference(lower)
    if brand_pref:
        merged["brand_preference"] = brand_pref

    # Structured option answers like "No preference" should resolve the last
    # asked field to prevent repeated mandatory-question loops.
    if _is_no_preference_response(lower):
        merged = _apply_no_preference_answer(merged)

    explicit_hard_fields = _explicit_hard_constraints_in_message(
        origin=origin,
        origin_scope=origin_scope,
        chocolate_type=choc_type,
        budget=budget,
        dietary=dietary,
        certification=certification,
    )
    if explicit_hard_fields:
        tracked = _explicit_hard_fields(merged)
        tracked.update(explicit_hard_fields)
        merged["_explicit_hard_fields"] = ",".join(sorted(tracked))

    return merged


def build_agentic_filters(state: Optional[dict]) -> Dict[str, dict]:
    normalized = normalize_state(state)
    segment = normalized.get("segment", "")
    tracked_explicit = _explicit_hard_fields(normalized)

    explicit_hard = {}
    for field in HARD_CONSTRAINT_FIELDS:
        value = normalized.get(field, "")
        if not _is_effective_constraint_value(field, value):
            continue
        if field in tracked_explicit:
            explicit_hard[field] = value

    inferred_hard = {}
    for field in HARD_CONSTRAINT_FIELDS:
        if field in explicit_hard:
            continue
        value = normalized.get(field, "")
        if not _is_effective_constraint_value(field, value):
            continue
        inferred_hard[field] = value

    hard_filters = {}
    hard_filters.update(explicit_hard)
    hard_filters.update(inferred_hard)

    required_fields = SEGMENT_REQUIRED_FIELDS.get(segment, [])
    required_constraints = {
        field: hard_filters[field]
        for field in required_fields
        if field in hard_filters
    }

    soft_weights = {}
    for field in SOFT_PREFERENCE_FIELDS:
        value = normalized.get(field, "")
        if _is_effective_constraint_value(field, value):
            soft_weights[field] = value

    return {
        "explicit": explicit_hard,
        "hard": hard_filters,
        "required": required_constraints,
        "soft": soft_weights,
    }


def build_agentic_retrieval_query(
    user_message: str,
    state: Optional[dict],
    include_soft_preferences: bool = True,
    include_context: bool = True,
) -> str:
    normalized = normalize_state(state)
    parts = [(user_message or "").strip()]

    filter_bundle = build_agentic_filters(normalized)
    explicit_hard = filter_bundle.get("explicit", {})
    hard = filter_bundle.get("hard", {})
    required = filter_bundle.get("required", {})
    soft = filter_bundle.get("soft", {})

    # 1) Explicit user constraints
    for field, value in explicit_hard.items():
        parts.append(_query_phrase_for_constraint(field, value))

    # 2) Remaining hard constraints
    for field, value in hard.items():
        if field in explicit_hard:
            continue
        parts.append(_query_phrase_for_constraint(field, value))

    # 3) Segment required constraints
    for field, value in required.items():
        if field in hard:
            continue
        parts.append(_query_phrase_for_constraint(field, value))

    # 4) Soft preferences
    if include_soft_preferences:
        for field, value in soft.items():
            parts.append(_query_phrase_for_constraint(field, value))

    if normalized["cocoa_percentage"]:
        parts.append(f"cocoa: {normalized['cocoa_percentage']}")
    if include_context and normalized["context"]:
        parts.append(f"context: {normalized['context']}")

    return " | ".join([p for p in parts if p])


def compute_missing_required_fields(state: Dict[str, str]) -> List[str]:
    segment = state.get("segment", "")
    required = SEGMENT_REQUIRED_FIELDS.get(segment, [])
    return [field for field in required if not _has_value(state.get(field, ""))]


def get_clarification_turns(state: Dict[str, str]) -> int:
    raw = state.get("_clarification_turns", "0")
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return 0


def get_ambiguous_turns(state: Dict[str, str]) -> int:
    raw = state.get("_ambiguous_turns", "0")
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return 0


def agent_step(
    user_message: str,
    state: dict,
    candidate_count: int,
    total_catalog_count: Optional[int] = None,
) -> dict:
    """Main agentic policy function.

    ASK return shape:
    {
      "action": "ASK",
      "question": str,
      "answer_options": list[str],
      "updated_state": dict
    }
    """
    updated_state = update_state_from_message(user_message, state)
    segment = updated_state.get("segment", "")
    filters = build_agentic_filters(updated_state)
    clarification_turns = get_clarification_turns(updated_state)
    missing_required = compute_missing_required_fields(updated_state)
    ambiguous_any = _is_any_ambiguous_response(user_message)
    ambiguous_turns = get_ambiguous_turns(updated_state)
    if ambiguous_any:
        ambiguous_turns += 1
    else:
        ambiguous_turns = 0
    updated_state["_ambiguous_turns"] = str(ambiguous_turns)
    retrieve_threshold = _dynamic_retrieve_threshold(total_catalog_count)
    early_retrieve_threshold = _early_direct_retrieve_threshold(total_catalog_count)
    missing_optional = _apply_ambiguity_helper(
        user_message,
        updated_state,
        _missing_optional_fields(segment, updated_state),
    )

    # Dynamic early stop: when candidate pool is very small, skip additional
    # clarification and move directly to retrieval.
    if 0 < candidate_count <= early_retrieve_threshold and not ambiguous_any:
        return {
            "action": "RETRIEVE",
            "question": "",
            "answer_options": [],
            "filters": filters,
            "updated_state": updated_state,
        }

    # Explicit country constraint disambiguation should happen before segment flow.
    if _has_value(updated_state.get("origin", "")) and not _has_value(updated_state.get("origin_scope", "")):
        asked_fields = _asked_fields(updated_state)
        if "origin_scope" in asked_fields and (user_message or "").strip():
            # Fail-safe against repeated loops: if we already asked the scope and
            # still cannot parse the reply, default to maker-country interpretation
            # and continue narrowing instead of asking the same question forever.
            updated_state["origin_scope"] = "maker_country"
            filters = build_agentic_filters(updated_state)
        else:
            updated_state = _record_question(updated_state, "origin_scope")
            return {
                "action": "ASK",
                "question": ORIGIN_SCOPE_QUESTION,
                "answer_options": _answer_options_for_field("origin_scope"),
                "filters": filters,
                "updated_state": updated_state,
            }

    # Segment handling:
    # - free_text mode (default): infer segment silently from message/state.
    # - clickbox mode: ask explicit A/B/C prompt first.
    if segment not in SEGMENT_REQUIRED_FIELDS:
        if _segment_mode() == "clickbox":
            # To prevent dead loops, if this prompt was already asked and still
            # unresolved, infer a best-effort segment and continue.
            if "segment" in _asked_fields(updated_state) and (user_message or "").strip():
                inferred_segment = _infer_segment_from_state(updated_state) or _infer_segment_from_message(user_message)
                if inferred_segment:
                    updated_state["segment"] = inferred_segment
                    segment = inferred_segment
                else:
                    updated_state["segment"] = "Impulsive-Involved"
                    segment = "Impulsive-Involved"
                filters = build_agentic_filters(updated_state)
                missing_required = compute_missing_required_fields(updated_state)
                missing_optional = _apply_ambiguity_helper(
                    user_message,
                    updated_state,
                    _missing_optional_fields(segment, updated_state),
                )
            else:
                updated_state = _record_asked_field(updated_state, "segment", increment_turn=False)
                return {
                    "action": "ASK",
                    "question": SEGMENT_SELECTION_PROMPT,
                    "answer_options": ["A", "B", "C"],
                    "filters": filters,
                    "updated_state": updated_state,
                }
        else:
            inferred_segment = _infer_segment_from_state(updated_state) or _infer_segment_from_message(user_message)
            updated_state["segment"] = inferred_segment or "Impulsive-Involved"
            segment = updated_state["segment"]
            filters = build_agentic_filters(updated_state)
            missing_required = compute_missing_required_fields(updated_state)
            missing_optional = _apply_ambiguity_helper(
                user_message,
                updated_state,
                _missing_optional_fields(segment, updated_state),
            )

    # In free-text mode, start with a richer open-ended narrowing question when
    # the scope is still broad. This feels closer to a human sommelier intake.
    asked_fields = _asked_fields(updated_state)
    if (
        _segment_mode() == "free_text"
        and clarification_turns == 0
        and not missing_required
        and candidate_count >= max(retrieve_threshold + 1, BROAD_NARROWING_MIN_CANDIDATES)
        and "broad_narrowing" not in asked_fields
    ):
        updated_state = _record_question(updated_state, "broad_narrowing")
        return {
            "action": "ASK",
            "question": _build_broad_narrowing_question(segment, candidate_count, updated_state),
            "answer_options": [],
            "filters": filters,
            "updated_state": updated_state,
        }

    # Ambiguity handling: first ambiguous answer keeps narrowing by asking one
    # more concrete question; repeated ambiguity falls back to tasting flight.
    if ambiguous_any and clarification_turns >= 1 and not missing_required:
        if missing_optional:
            field = missing_optional[0]
            question = _question_for_field(segment, field, updated_state)
            updated_state = _record_question(updated_state, field)
            return {
                "action": "ASK",
                "question": question,
                "answer_options": _answer_options_for_field(field),
                "filters": filters,
                "updated_state": updated_state,
            }
        if ambiguous_turns >= 2:
            return {
                "action": "RETRIEVE",
                "question": "",
                "answer_options": [],
                "filters": filters,
                "updated_state": updated_state,
                "fallback_mode": "TASTING_FLIGHT",
            }

    # If user explicitly asks for recommendations after at least one
    # clarification turn, proceed to retrieval with current constraints.
    if (
        _is_direct_recommendation_request(user_message)
        and clarification_turns >= 1
        and _has_any_constraints(filters)
    ):
        return {
            "action": "RETRIEVE",
            "question": "",
            "answer_options": [],
            "filters": filters,
            "updated_state": updated_state,
        }

    # Stop rules based on database narrowing quality:
    # - retrieve when candidate scope is already narrow enough
    # - or we reached the max clarification turns
    if candidate_count <= retrieve_threshold or clarification_turns >= MAX_CLARIFICATION_QUESTIONS:
        return {
            "action": "RETRIEVE",
            "question": "",
            "answer_options": [],
            "filters": filters,
            "updated_state": updated_state,
        }

    # If scope is still broad, ask one optional calibration question first.
    if (
        not missing_required
        and clarification_turns == 0
        and missing_optional
    ):
        field = missing_optional[0]
        question = _question_for_field(segment, field, updated_state)
        updated_state = _record_question(updated_state, field)
        return {
            "action": "ASK",
            "question": question,
            "answer_options": _answer_options_for_field(field),
            "filters": filters,
            "updated_state": updated_state,
        }

    # Required field collection step.
    # Never ask the same required field in a loop. If a required field was already
    # asked but remains unresolved, auto-relax to a neutral value and continue.
    if missing_required:
        asked_fields = _asked_fields(updated_state)
        unasked_required = [field for field in missing_required if field not in asked_fields]
        if not unasked_required:
            for field in missing_required:
                updated_state = _apply_unresolved_required_fallback(updated_state, field)
            filters = build_agentic_filters(updated_state)
            missing_required = compute_missing_required_fields(updated_state)
        else:
            field = unasked_required[0]
            question = _question_for_field(segment, field, updated_state)
            updated_state = _record_question(updated_state, field)
            return {
                "action": "ASK",
                "question": question,
                "answer_options": _answer_options_for_field(field),
                "filters": filters,
                "updated_state": updated_state,
            }

    if missing_required:
        # Safety net: if anything still unresolved after fallback, retrieve
        # instead of repeating asks.
        return {
            "action": "RETRIEVE",
            "question": "",
            "answer_options": [],
            "filters": filters,
            "updated_state": updated_state,
        }

    # Continue narrowing with optional preferences when scope is still broad.
    if missing_optional:
        field = missing_optional[0]
        question = _question_for_field(segment, field, updated_state)
        updated_state = _record_question(updated_state, field)
        return {
            "action": "ASK",
            "question": question,
            "answer_options": _answer_options_for_field(field),
            "filters": filters,
            "updated_state": updated_state,
        }

    return {
        "action": "RETRIEVE",
        "question": "",
        "answer_options": [],
        "filters": filters,
        "updated_state": updated_state,
    }


def _apply_ambiguity_helper(
    user_message: str,
    state: Dict[str, str],
    fallback_missing: List[str],
) -> List[str]:
    if not fallback_missing:
        return []
    if not _AMBIGUITY_HELPER:
        return fallback_missing

    try:
        result = _AMBIGUITY_HELPER(user_message, state, fallback_missing)
    except Exception:
        return fallback_missing

    if not isinstance(result, dict):
        return fallback_missing

    needs = bool(result.get("needs_more_info"))
    llm_missing = result.get("missing_fields")
    if not needs or not isinstance(llm_missing, list):
        return fallback_missing

    # Keep only fields that belong to the active segment, are still empty,
    # and were not already asked in this clarification journey.
    segment = state.get("segment", "")
    asked = _asked_fields(state)
    allowed = set(SEGMENT_OPTIONAL_FIELDS.get(segment, []) + SEGMENT_REQUIRED_FIELDS.get(segment, []))
    valid = [
        f
        for f in llm_missing
        if (
            isinstance(f, str)
            and f in allowed
            and f not in asked
            and not _has_value(state.get(f, ""))
        )
    ]
    return valid or fallback_missing


def _question_for_field(segment: str, field: str, state: Dict[str, str]) -> str:
    question = QUESTION_TEXT.get(segment, {}).get(field, "Could you share one more preference?")
    if state.get("context") != "gift":
        return question

    if segment == "Rational Health-Conscious" and field == "certification":
        return f"{question} Also, should gift packaging be eco-friendly?"
    if segment == "Impulsive-Involved" and field in {"chocolate_type", "flavor_direction"}:
        return f"{question} And should I prioritize gift presentation too?"
    if segment == "Uninvolved" and field == "budget":
        return "What budget range are you considering for a gift-ready option?"

    return question


def _answer_options_for_field(field: str) -> List[str]:
    if field == "origin_scope":
        return [
            "Made in that country",
            "Cocoa bean origin from that country",
        ]
    return list(ANSWER_OPTIONS_BY_FIELD.get(field, []))


def _missing_optional_fields(segment: str, state: Dict[str, str]) -> List[str]:
    optional_fields = SEGMENT_OPTIONAL_FIELDS.get(segment, [])
    asked = _asked_fields(state)
    missing = []
    for field in optional_fields:
        if _has_value(state.get(field, "")):
            continue
        if field in asked:
            continue
        missing.append(field)
    return missing


def _record_question(state: Dict[str, str], field: str) -> Dict[str, str]:
    return _record_asked_field(state, field, increment_turn=True)


def _record_asked_field(
    state: Dict[str, str],
    field: str,
    increment_turn: bool = True,
) -> Dict[str, str]:
    updated = normalize_state(state)
    if increment_turn:
        turns = get_clarification_turns(updated)
        updated["_clarification_turns"] = str(turns + 1)

    asked = _asked_fields(updated)
    asked.add(field)
    updated["_asked_fields"] = ",".join(sorted(asked))
    updated["_last_asked_field"] = field
    return updated


def _asked_fields(state: Dict[str, str]) -> Set[str]:
    raw = state.get("_asked_fields", "")
    if not raw:
        return set()
    return {chunk.strip() for chunk in raw.split(",") if chunk.strip()}


def _explicit_hard_fields(state: Dict[str, str]) -> Set[str]:
    raw = state.get("_explicit_hard_fields", "")
    if not raw:
        return set()
    return {chunk.strip() for chunk in raw.split(",") if chunk.strip()}


def _explicit_hard_constraints_in_message(
    origin: str,
    origin_scope: str,
    chocolate_type: str,
    budget: str,
    dietary: str,
    certification: str,
) -> Set[str]:
    explicit: Set[str] = set()
    if _has_value(origin):
        explicit.add("origin")
    if _has_value(origin_scope):
        explicit.add("origin_scope")
    if _has_value(chocolate_type):
        explicit.add("chocolate_type")
    if _has_value(budget):
        explicit.add("budget")
    if _has_value(dietary):
        explicit.add("dietary")
    if _has_value(certification):
        explicit.add("certification")
    return explicit


def _query_phrase_for_constraint(field: str, value: str) -> str:
    if field == "origin":
        return f"origin: {value}"
    if field == "origin_scope":
        return f"origin scope: {value}"
    if field == "chocolate_type":
        return str(value)
    if field == "budget":
        return f"budget: {value}"
    if field == "dietary":
        return f"dietary: {value}"
    if field == "certification":
        return f"certification: {value}"
    if field == "flavor_direction":
        return f"flavor: {value}"
    if field == "intensity":
        return f"intensity: {value}"
    if field == "brand_preference":
        return f"brand preference: {value}"
    return f"{field}: {value}"


def _extract_chocolate_type(lower: str) -> str:
    if re.search(r"\b(dark|noir)\b", lower):
        return "dark"
    if re.search(r"\b(milk|lait)\b", lower):
        return "milk"
    if re.search(r"\b(white|blanc)\b", lower):
        return "white"
    return ""


def _extract_origin(lower: str) -> str:
    # Common country + demonym aliases; values are canonical country labels.
    origin_aliases = {
        "france": "France",
        "french": "France",
        "usa": "USA",
        "u.s.a": "USA",
        "us": "USA",
        "u.s": "USA",
        "united states": "USA",
        "america": "USA",
        "american": "USA",
        "uk": "UK",
        "united kingdom": "UK",
        "britain": "UK",
        "england": "UK",
        "italy": "Italy",
        "italian": "Italy",
        "belgium": "Belgium",
        "belgian": "Belgium",
        "switzerland": "Switzerland",
        "swiss": "Switzerland",
        "japan": "Japan",
        "japanese": "Japan",
        "spain": "Spain",
        "spanish": "Spain",
        "germany": "Germany",
        "german": "Germany",
        "canada": "Canada",
        "canadian": "Canada",
        "brazil": "Brazil",
        "brazilian": "Brazil",
        "peru": "Peru",
        "peruvian": "Peru",
        "ecuador": "Ecuador",
        "ecuadorian": "Ecuador",
        "venezuela": "Venezuela",
        "venezuelan": "Venezuela",
        "madagascar": "Madagascar",
        "madagascan": "Madagascar",
        "austria": "Austria",
        "austrian": "Austria",
        "mexico": "Mexico",
        "mexican": "Mexico",
        "india": "India",
        "indian": "India",
        "ghana": "Ghana",
        "ghanian": "Ghana",
    }

    for alias, canonical in sorted(origin_aliases.items(), key=lambda x: len(x[0]), reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", lower):
            return canonical

    # Generic fallback for "from X" and "made in X" phrasing.
    match = re.search(r"\b(?:from|made in|produced in)\s+([a-z][a-z\s\-']{2,30})", lower)
    if not match:
        return ""

    candidate = re.sub(r"\s+", " ", match.group(1)).strip(" .,!?:;")
    candidate = re.split(
        r"\b(?:for|with|under|over|above|below|that|which|who|because|while|gift|present|dad|mom|today)\b",
        candidate,
        maxsplit=1,
    )[0].strip(" .,!?:;")
    stopwords = {
        "our database",
        "the database",
        "today",
        "now",
        "here",
        "there",
        "that country",
        "this country",
    }
    if candidate in stopwords:
        return ""

    return candidate.title()


def _extract_origin_scope(lower: str) -> str:
    normalized = (lower or "").strip().lower()

    # Option-style answers from chat text.
    if re.fullmatch(r"(?:option\s*)?1[\)\.\:]?\s*", normalized):
        return "maker_country"
    if re.fullmatch(r"(?:option\s*)?2[\)\.\:]?\s*", normalized):
        return "origin_country"

    if re.match(r"^\s*(?:option\s*)?1[\)\.\:]?", normalized) and any(
        token in normalized for token in ["made", "brand", "brands", "manufacturer", "manufacturers", "maker"]
    ):
        return "maker_country"
    if re.match(r"^\s*(?:option\s*)?2[\)\.\:]?", normalized) and any(
        token in normalized for token in ["bean", "cocoa", "origin", "source", "sourced"]
    ):
        return "origin_country"

    maker_patterns = [
        r"\bmade by\b",
        r"\bmade in\b",
        r"\bmanufacturers?\b",
        r"\bmaker\b",
        r"\bbrands?\b",
        r"\bmade in that country\b",
    ]
    bean_patterns = [
        r"\bbean origin\b",
        r"\bcocoa bean\b",
        r"\bcocoa origin\b",
        r"\borigin country\b",
        r"\bsourced from\b",
        r"\bfrom that country\b",
    ]

    if any(re.search(p, normalized) for p in maker_patterns):
        return "maker_country"
    if any(re.search(p, normalized) for p in bean_patterns):
        return "origin_country"
    if "made in that country" in normalized:
        return "maker_country"
    if "cocoa bean origin from that country" in normalized:
        return "origin_country"
    return ""


def _extract_flavor_direction(lower: str) -> str:
    flavors = []
    if any(k in lower for k in ["sweet", "sucre", "honey", "toffee"]):
        flavors.append("sweet")
    if any(k in lower for k in ["fruity", "fruit", "fruité", "berry", "citrus", "fig", "figue", "abricot", "raisin"]):
        flavors.append("fruity")
    if any(k in lower for k in ["nutty", "nut", "hazelnut", "almond", "noisette", "amande"]):
        flavors.append("nutty")
    if "caramel" in lower:
        flavors.append("caramel")
    if any(k in lower for k in ["spicy", "epice", "épice", "chili", "pepper", "cinnamon"]):
        flavors.append("spicy")
    if "dark" in lower and "dark" not in flavors:
        flavors.append("dark")

    if not flavors:
        return ""
    return ", ".join(dict.fromkeys(flavors))


def _extract_intensity(lower: str) -> str:
    if any(k in lower for k in ["intense", "fort", "strong", "bold", "high intensity"]):
        return "intense"
    if any(k in lower for k in ["smooth", "creamy", "mild", "soft", "doux", "onctueux"]):
        return "smooth"
    return ""


def _extract_budget(lower: str) -> str:
    if re.search(r"\b(broaden|relax|widen|loosen)\b.*\bbudget\b", lower):
        return ""

    if any(phrase in lower for phrase in ["no budget limit", "any budget", "no limit"]):
        return "no budget limit"

    gt_match = re.search(r"(?:>=|>|over|above|at least|more than)\s*\$?\s*(\d+(?:\.\d+)?)", lower)
    if gt_match:
        return f"over ${gt_match.group(1)}"

    range_match = re.search(r"\$?\s*(\d+(?:\.\d+)?)\s*(?:-|to)\s*\$?\s*(\d+(?:\.\d+)?)", lower)
    if range_match:
        return f"${range_match.group(1)}-${range_match.group(2)}"

    max_match = re.search(r"(?:under|below|less than|max)\s*\$?\s*(\d+(?:\.\d+)?)", lower)
    if max_match:
        return f"under ${max_match.group(1)}"

    min_match = re.search(r"(?:over|above|at least|more than)\s*\$?\s*(\d+(?:\.\d+)?)", lower)
    if min_match:
        return f"over ${min_match.group(1)}"

    dollar_value = re.search(r"\$\s*(\d+(?:\.\d+)?)", lower)
    if dollar_value:
        return f"around ${dollar_value.group(1)}"

    if any(k in lower for k in ["cheap", "affordable", "budget-friendly", "low cost"]):
        return "budget-friendly"
    if any(k in lower for k in ["premium", "luxury", "high-end", "expensive", "higher budget", "more expensive"]):
        return "premium"
    return ""


def _extract_certification(lower: str, segment: str, last_asked_field: str = "") -> str:
    if re.search(r"\b(no|not)\s+(certification|certifications|organic|fair trade)\b", lower):
        return "not required"

    certs = []
    if "organic" in lower:
        certs.append("organic")
    if "fair trade" in lower or "fairtrade" in lower:
        certs.append("fair trade")
    if "sustainability" in lower or "sustainable" in lower:
        certs.append("sustainability")
    if "ethical" in lower:
        certs.append("ethical sourcing")

    if certs:
        return ", ".join(dict.fromkeys(certs))

    # Only map bare yes/no to certification when the last asked field was certification.
    # This avoids corrupting state when user says "no" to cocoa percentage question.
    if last_asked_field == "certification" and re.search(r"\b(not sure|unsure|don't know|dont know)\b", lower):
        return ""
    if (
        segment == "Rational Health-Conscious"
        and last_asked_field == "certification"
        and re.search(r"\b(yes|sure|important|yep)\b", lower)
    ):
        return "important"
    if (
        segment == "Rational Health-Conscious"
        and last_asked_field == "certification"
        and re.search(r"\b(no|not really|doesn'?t matter)\b", lower)
    ):
        return "not required"
    return ""


def _extract_dietary(lower: str) -> str:
    tags = []
    if "vegan" in lower:
        tags.append("vegan")
    if "low sugar" in lower or "less sugar" in lower or "sugar-free" in lower:
        tags.append("low sugar")
    if "dairy-free" in lower or "dairy free" in lower:
        tags.append("dairy-free")
    if "gluten-free" in lower or "gluten free" in lower:
        tags.append("gluten-free")
    if "keto" in lower:
        tags.append("keto")

    return ", ".join(tags)


def _extract_cocoa_percentage(lower: str) -> str:
    exact = re.search(r"\b(\d{1,3})\s?%", lower)
    if exact:
        return f"{exact.group(1)}%"
    if "high cocoa" in lower:
        return "high cocoa"
    if "low cocoa" in lower:
        return "low cocoa"
    return ""


def _extract_brand_preference(lower: str) -> str:
    if any(k in lower for k in ["familiar", "trusted", "mainstream", "known brands"]):
        return "familiar"
    if any(k in lower for k in ["open", "discover", "new brand", "something new"]):
        return "open"
    return ""


def _has_gift_context(lower: str) -> bool:
    return bool(re.search(r"\b(gift|birthday|present|anniversary|celebration)\b", lower))


def _is_any_ambiguous_response(user_message: str) -> bool:
    lower = (user_message or "").strip().lower()
    if not lower:
        return False
    return any(re.search(pattern, lower) for pattern in AMBIGUOUS_ANY_PATTERNS)


def _has_value(value: str) -> bool:
    return bool(str(value).strip())


def _is_effective_constraint_value(field: str, value: str) -> bool:
    text = str(value or "").strip().lower()
    if not text:
        return False
    if field == "certification" and text == "not required":
        return False
    if field == "budget" and text == "no budget limit":
        return False
    return text not in NON_CONSTRAINT_VALUES


def _extract_relax_targets(lower: str) -> Set[str]:
    text = (lower or "").strip().lower()
    if not text:
        return set()
    if not re.search(r"\b(broaden|relax|widen|loosen)\b", text):
        return set()

    targets: Set[str] = set()
    if "budget" in text:
        targets.add("budget")
    if "certification" in text or "certifications" in text:
        targets.add("certification")
    if "dietary" in text or "diet" in text:
        targets.add("dietary")
    if "cocoa" in text:
        targets.add("cocoa_percentage")
        targets.add("intensity")
    if "intensity" in text:
        targets.add("intensity")
    if "flavor" in text or "taste" in text:
        targets.add("flavor_direction")
    if "brand" in text:
        targets.add("brand_preference")
    if "origin" in text or "country" in text:
        targets.add("origin")
        targets.add("origin_scope")
    if "type" in text or "milk" in text or "dark" in text or "white" in text:
        targets.add("chocolate_type")
    return targets


def _apply_relaxation(state: Dict[str, str], targets: Set[str]) -> Dict[str, str]:
    updated = normalize_state(state)
    for field in targets:
        if field == "budget":
            updated["budget"] = "no budget limit"
        elif field == "certification":
            updated["certification"] = "not required"
        elif field in updated:
            updated[field] = ""

    tracked = _explicit_hard_fields(updated)
    for field in targets:
        tracked.discard(field)
    updated["_explicit_hard_fields"] = ",".join(sorted(tracked))
    return updated


def _is_no_preference_response(lower: str) -> bool:
    text = (lower or "").strip().lower()
    if not text:
        return False
    return bool(
        re.search(r"\b(no preference|any|whatever|up to you|doesn'?t matter|dont care|don't care)\b", text)
        or text in {"not sure", "i dont know", "i don't know"}
    )


def _apply_no_preference_answer(state: Dict[str, str]) -> Dict[str, str]:
    updated = normalize_state(state)
    last_field = updated.get("_last_asked_field", "")
    if not last_field:
        return updated
    if last_field == "budget":
        updated["budget"] = "no budget limit"
    elif last_field == "certification":
        updated["certification"] = "not required"
    elif last_field in updated:
        updated[last_field] = "no preference"
    return updated


def _apply_unresolved_required_fallback(state: Dict[str, str], field: str) -> Dict[str, str]:
    updated = normalize_state(state)
    if field == "budget":
        updated["budget"] = "no budget limit"
    elif field == "certification":
        updated["certification"] = "not required"
    elif field in updated:
        updated[field] = "no preference"
    return updated


def _build_broad_narrowing_question(segment: str, candidate_count: int, state: Dict[str, str]) -> str:
    intro = (
        f"I currently see about {candidate_count} relevant options. "
        "To narrow quickly, tell me one or two priorities:"
    )
    if segment == "Rational Health-Conscious":
        points = [
            "- Certification priorities (organic, fair trade, sustainability)",
            "- Dietary needs (vegan, low sugar, dairy-free)",
            "- Cocoa level (for example 70%+ or smoother style)",
            "- Budget or gift context",
        ]
    elif segment == "Uninvolved":
        points = [
            "- Budget range",
            "- Familiar brands vs discovering new ones",
            "- Chocolate type (dark, milk, white)",
            "- Everyday treat or gift",
        ]
    else:
        points = [
            "- Flavor direction (fruity, nutty, caramel, spicy, floral)",
            "- Intensity (bold vs smooth)",
            "- Origin preference (maker country or bean origin)",
            "- Budget or gift context",
        ]
    return intro + "\n" + "\n".join(points)


def _is_direct_recommendation_request(user_message: str) -> bool:
    lower = (user_message or "").strip().lower()
    if not lower:
        return False
    return bool(
        re.search(
            r"\b(recommend|recommendation|recommande|recommandation|suggest|suggere|suggère|conseille|propose|show me|give me|pick for me)\b",
            lower,
        )
        or lower in {"recommend", "suggest", "show options", "give me options", "recommande", "propose"}
    )


def _has_any_constraints(filters: Dict[str, dict]) -> bool:
    for bucket in ("explicit", "hard", "soft", "required"):
        data = filters.get(bucket, {})
        if isinstance(data, dict) and any(str(v).strip() for v in data.values()):
            return True
    return False


def _infer_segment_from_state(state: Dict[str, str]) -> str:
    # Best-effort segment inference to avoid repeated segment prompts.
    if _has_value(state.get("certification", "")) or _has_value(state.get("dietary", "")):
        return "Rational Health-Conscious"
    if _has_value(state.get("budget", "")) or _has_value(state.get("brand_preference", "")):
        return "Uninvolved"
    if (
        _has_value(state.get("chocolate_type", ""))
        or _has_value(state.get("flavor_direction", ""))
        or _has_value(state.get("intensity", ""))
    ):
        return "Impulsive-Involved"
    return ""


def _infer_segment_from_message(user_message: str) -> str:
    lower = (user_message or "").strip().lower()
    if not lower:
        return ""

    scores = {
        "Impulsive-Involved": 0,
        "Rational Health-Conscious": 0,
        "Uninvolved": 0,
    }

    for token in ["organic", "fair trade", "fairtrade", "sustainable", "ethical", "vegan", "dietary", "low sugar", "dairy-free", "gluten-free", "healthy"]:
        if token in lower:
            scores["Rational Health-Conscious"] += 1
    for token in ["bio", "equitable", "équitable", "vegan", "vegane", "sain", "sante", "santé"]:
        if token in lower:
            scores["Rational Health-Conscious"] += 1

    for token in ["budget", "cheap", "affordable", "value", "familiar brand", "mainstream", "trusted brand", "low cost", "price"]:
        if token in lower:
            scores["Uninvolved"] += 1
    for token in ["prix", "pas cher", "bon rapport qualite", "bon rapport qualité"]:
        if token in lower:
            scores["Uninvolved"] += 1

    for token in ["dark", "milk", "white", "flavor", "taste", "fruity", "nutty", "caramel", "spicy", "intense", "smooth", "creamy"]:
        if token in lower:
            scores["Impulsive-Involved"] += 1
    for token in ["noir", "lait", "blanc", "gout", "goût", "fruité", "noisette", "amande", "intense", "doux"]:
        if token in lower:
            scores["Impulsive-Involved"] += 1

    best_segment = max(scores, key=scores.get)
    return best_segment if scores[best_segment] > 0 else ""


def _dynamic_retrieve_threshold(total_catalog_count: Optional[int]) -> int:
    if not total_catalog_count or total_catalog_count <= 0:
        return CANDIDATE_RETRIEVE_THRESHOLD

    scaled = int(round(total_catalog_count * CATALOG_RETRIEVE_RATIO))
    return max(MIN_DYNAMIC_RETRIEVE_THRESHOLD, min(CANDIDATE_RETRIEVE_THRESHOLD, scaled))


def _early_direct_retrieve_threshold(total_catalog_count: Optional[int]) -> int:
    if not total_catalog_count or total_catalog_count <= 0:
        return EARLY_DIRECT_RETRIEVE_THRESHOLD

    # Keep this strict: "small pool" means only a handful of viable products.
    scaled = int(round(total_catalog_count * 0.004))
    return max(3, min(EARLY_DIRECT_RETRIEVE_THRESHOLD, scaled))
