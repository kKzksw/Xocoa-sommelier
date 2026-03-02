"""
Segment-aware clarification logic used before retrieval.

This module keeps the logic lightweight and deterministic so it can run
on every request without adding model calls.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional


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
    "taste",
    "budget",
    "certification",
    "dietary",
    "cocoa_percentage",
    "intensity",
    "brand_preference",
]

SEGMENT_REQUIRED_FIELDS = {
    "Rational Health-Conscious": ["certification"],
    "Impulsive-Involved": ["taste"],
    "Uninvolved": ["budget"],
}

SEGMENT_OPTIONAL_FIELDS = {
    "Rational Health-Conscious": ["dietary", "cocoa_percentage"],
    "Impulsive-Involved": ["intensity"],
    "Uninvolved": ["brand_preference"],
}

QUESTIONS_BY_SEGMENT = {
    "Rational Health-Conscious": {
        "required": {
            "certification": (
                "Are certifications important to you (organic, fair trade, sustainability)?"
            )
        },
        "optional": [
            "Do you have any dietary preferences (vegan, low sugar, dairy-free, etc.)?",
            "Are you looking for a specific cocoa percentage or intensity?",
        ],
    },
    "Impulsive-Involved": {
        "required": {
            "taste": (
                "What flavor direction do you prefer? Sweet / Dark / Fruity / Nutty / Caramel / Spicy?"
            )
        },
        "optional": [
            "Do you enjoy intense chocolate or something smoother and creamy?",
            "Is this for a romantic gift, a celebration, or a casual treat?",
        ],
    },
    "Uninvolved": {
        "required": {"budget": "What budget range are you considering?"},
        "optional": [
            "Do you prefer familiar brands or are you open to discovering something new?",
            "Is this for everyday enjoyment or a gift?",
        ],
    },
}


def default_state() -> Dict[str, str]:
    return {field: "" for field in STATE_FIELDS}


def get_segment_selection_prompt() -> str:
    return SEGMENT_SELECTION_PROMPT


def normalize_state(state: Optional[dict]) -> Dict[str, str]:
    """
    Always return a full state shape so endpoint logic can stay simple.
    """
    normalized = default_state()
    if not isinstance(state, dict):
        return normalized

    for field in STATE_FIELDS:
        value = state.get(field, "")
        normalized[field] = "" if value is None else str(value).strip()
    return normalized


def detect_segment_from_clickbox(user_message: str) -> Optional[str]:
    """
    Map click-box selection (A/B/C or option text) to internal segment.
    """
    text = (user_message or "").strip().lower()
    if not text:
        return None

    # Handles "A", "a)", "option b", "C."
    letter_match = re.fullmatch(r"(?:option\s*)?([abc])[\)\.\:]?", text)
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
    """
    Parse structured preference signals from user free-text and merge into state.
    """
    merged = normalize_state(state)
    text = (user_message or "").strip()
    lower = text.lower()

    detected_segment = detect_segment_from_clickbox(text)
    if detected_segment:
        merged["segment"] = detected_segment

    if _has_gift_context(lower):
        merged["context"] = "gift"
    elif any(k in lower for k in ["everyday", "daily", "casual treat"]):
        merged["context"] = "everyday"

    taste_matches = _extract_taste_preferences(lower)
    if taste_matches:
        merged["taste"] = ", ".join(taste_matches)

    budget = _extract_budget(lower)
    if budget:
        merged["budget"] = budget

    certification = _extract_certification(lower, merged.get("segment", ""))
    if certification:
        merged["certification"] = certification

    dietary = _extract_dietary(lower)
    if dietary:
        merged["dietary"] = dietary

    cocoa = _extract_cocoa_percentage(lower)
    if cocoa:
        merged["cocoa_percentage"] = cocoa

    intensity = _extract_intensity(lower)
    if intensity:
        merged["intensity"] = intensity

    brand_pref = _extract_brand_preference(lower)
    if brand_pref:
        merged["brand_preference"] = brand_pref

    return merged


def build_retrieval_query(user_message: str, state: Optional[dict]) -> str:
    """
    Merge conversational memory into retrieval text so Channel A/B can use it.
    """
    normalized = normalize_state(state)
    parts = [(user_message or "").strip()]

    if normalized["taste"]:
        parts.append(f"taste: {normalized['taste']}")
    if normalized["budget"]:
        parts.append(f"budget: {normalized['budget']}")
    if normalized["certification"]:
        parts.append(f"certification: {normalized['certification']}")
    if normalized["dietary"]:
        parts.append(f"dietary: {normalized['dietary']}")
    if normalized["cocoa_percentage"]:
        parts.append(f"cocoa: {normalized['cocoa_percentage']}")
    if normalized["intensity"]:
        parts.append(f"intensity: {normalized['intensity']}")
    if normalized["brand_preference"]:
        parts.append(f"brand preference: {normalized['brand_preference']}")
    if normalized["context"]:
        parts.append(f"context: {normalized['context']}")

    return " | ".join([p for p in parts if p])


def check_clarification(user_message: str, state: dict) -> dict:
    """
    Return STRICT JSON-compatible dict:
    {
      "needs_clarification": bool,
      "followup_questions": list[str]
    }
    """
    normalized = normalize_state(state)
    segment = normalized.get("segment", "")

    if segment not in SEGMENT_REQUIRED_FIELDS:
        return {
            "needs_clarification": True,
            "followup_questions": [SEGMENT_SELECTION_PROMPT],
        }

    missing_required = [
        field
        for field in SEGMENT_REQUIRED_FIELDS[segment]
        if not _has_value(normalized.get(field, ""))
    ]
    ambiguous_query = _is_ambiguous_query(user_message, segment, normalized)

    if not missing_required and not ambiguous_query:
        return {
            "needs_clarification": False,
            "followup_questions": [],
        }

    followups = _build_followup_questions(
        segment=segment,
        state=normalized,
        missing_required=missing_required,
        ambiguous_query=ambiguous_query,
    )
    return {
        "needs_clarification": bool(followups),
        "followup_questions": followups[:3],
    }


def _build_followup_questions(
    segment: str,
    state: Dict[str, str],
    missing_required: List[str],
    ambiguous_query: bool,
) -> List[str]:
    bundle = QUESTIONS_BY_SEGMENT[segment]
    required_questions = bundle["required"]
    optional_questions = bundle["optional"]
    is_gift = state.get("context") == "gift"

    questions: List[str] = []

    # Required fields gate retrieval, so we ask those first.
    if missing_required:
        for field in missing_required:
            q = required_questions.get(field)
            if not q:
                continue
            questions.append(_apply_gift_modifier(segment, q, state))

        # We can add up to 2 more segment questions in the same clarification turn.
        # This keeps total questions <= 3 while collecting richer context early.
        questions.extend(_optional_question_bundle(segment, is_gift, optional_questions))
        return _dedupe_preserve_order(questions)[:3]

    if ambiguous_query:
        questions.extend(_optional_question_bundle(segment, is_gift, optional_questions))

    return _dedupe_preserve_order(questions)[:3]


def _optional_question_bundle(segment: str, is_gift: bool, optional_questions: List[str]) -> List[str]:
    if segment == "Rational Health-Conscious":
        questions = list(optional_questions)
        if is_gift:
            questions.append("Since this is a gift, is eco-friendly packaging important to you as well?")
        return questions

    if segment == "Impulsive-Involved":
        questions = [optional_questions[0]]
        if is_gift:
            questions.append("For this gift, should I prioritize bold flavor impact, elegant presentation, or both?")
        else:
            questions.append(optional_questions[1])
        return questions

    if segment == "Uninvolved":
        questions = [optional_questions[0]]
        if is_gift:
            questions.append("For a gift-ready option, do you want simple packaging or premium presentation?")
        else:
            questions.append(optional_questions[1])
        return questions

    return []


def _apply_gift_modifier(segment: str, question: str, state: Dict[str, str]) -> str:
    if state.get("context") != "gift":
        return question

    if segment == "Rational Health-Conscious":
        return f"{question} Also, should gift packaging be eco-friendly?"
    if segment == "Impulsive-Involved":
        return f"{question} And should I prioritize elegant gift presentation too?"
    if segment == "Uninvolved":
        if "budget range" in question.lower():
            return "What budget range are you considering for a gift-ready option?"
        return f"{question} Should I keep it gift-ready within your budget?"
    return question


def _is_ambiguous_query(user_message: str, segment: str, state: Dict[str, str]) -> bool:
    lower = (user_message or "").strip().lower()

    if detect_segment_from_clickbox(lower):
        return True

    # If any required field is already present, we do not consider this ambiguous.
    required = SEGMENT_REQUIRED_FIELDS.get(segment, [])
    if any(_has_value(state.get(field, "")) for field in required):
        return False

    generic_patterns = [
        r"^chocolate$",
        r"^recommend( me)?$",
        r"^anything$",
        r"^something good$",
        r"^help me choose$",
    ]
    if any(re.fullmatch(pattern, lower) for pattern in generic_patterns):
        return True

    tokens = [t for t in re.split(r"\s+", lower) if t]
    return len(tokens) <= 2


def _extract_taste_preferences(lower: str) -> List[str]:
    taste_map = {
        "sweet": ["sweet"],
        "dark": ["dark", "bitter"],
        "fruity": ["fruity", "fruit", "berry", "citrus"],
        "nutty": ["nutty", "nut", "hazelnut", "almond"],
        "caramel": ["caramel", "toffee"],
        "spicy": ["spicy", "chili", "pepper", "cinnamon"],
    }
    found: List[str] = []
    for label, keys in taste_map.items():
        if any(key in lower for key in keys):
            found.append(label)
    return found


def _extract_budget(lower: str) -> str:
    range_match = re.search(r"\$?\s*(\d+(?:\.\d+)?)\s*(?:-|to)\s*\$?\s*(\d+(?:\.\d+)?)", lower)
    if range_match:
        return f"${range_match.group(1)}-${range_match.group(2)}"

    max_match = re.search(r"(?:under|below|less than|max)\s*\$?\s*(\d+(?:\.\d+)?)", lower)
    if max_match:
        return f"under ${max_match.group(1)}"

    min_match = re.search(r"(?:over|above|at least)\s*\$?\s*(\d+(?:\.\d+)?)", lower)
    if min_match:
        return f"over ${min_match.group(1)}"

    dollar_value = re.search(r"\$\s*(\d+(?:\.\d+)?)", lower)
    if dollar_value:
        return f"around ${dollar_value.group(1)}"

    if any(k in lower for k in ["cheap", "affordable", "budget"]):
        return "budget-friendly"
    if any(k in lower for k in ["premium", "luxury", "high-end"]):
        return "premium"
    return ""


def _extract_certification(lower: str, segment: str) -> str:
    if re.search(r"\b(no|not)\s+(certification|certifications|organic|fair trade)\b", lower):
        return "not required"

    cert_keys = []
    if "organic" in lower:
        cert_keys.append("organic")
    if "fair trade" in lower or "fairtrade" in lower:
        cert_keys.append("fair trade")
    if "sustainability" in lower or "sustainable" in lower:
        cert_keys.append("sustainability")
    if "ethical" in lower:
        cert_keys.append("ethical sourcing")
    if "direct trade" in lower:
        cert_keys.append("direct trade")

    if cert_keys:
        return ", ".join(dict.fromkeys(cert_keys))

    # If user answers "yes/sure" to certification follow-up in this segment.
    if segment == "Rational Health-Conscious" and re.search(r"\b(yes|yep|sure|important)\b", lower):
        return "important"
    if segment == "Rational Health-Conscious" and re.search(r"\b(no|not really|doesn'?t matter)\b", lower):
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


def _extract_intensity(lower: str) -> str:
    if any(k in lower for k in ["intense", "strong", "bold"]):
        return "intense"
    if any(k in lower for k in ["smooth", "creamy", "mild"]):
        return "smooth"
    return ""


def _extract_brand_preference(lower: str) -> str:
    if any(k in lower for k in ["familiar brand", "familiar", "trusted", "mainstream"]):
        return "familiar"
    if any(k in lower for k in ["open", "discover", "new brand", "something new"]):
        return "open"
    return ""


def _has_gift_context(lower: str) -> bool:
    return bool(re.search(r"\b(gift|birthday|present|anniversary|celebration)\b", lower))


def _has_value(value: str) -> bool:
    return bool(str(value).strip())


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    output = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output
