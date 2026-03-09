"""Conversational sommelier policy helpers.

This module only controls conversational behavior (what to ask next and how to
phrase it). It does not change retrieval architecture.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Dict, Iterable, List, Tuple


_AMBIGUOUS_PATTERNS = [
    r"\bany\b",
    r"\banything\b",
    r"\bwhatever\b",
    r"\bnot sure\b",
    r"\bi don'?t know\b",
    r"\bup to you\b",
]


def describe_candidate_pool(candidate_count: int, applied_filters: Dict[str, str]) -> str:
    """Describe current search scope in sommelier tone."""
    count = max(0, int(candidate_count or 0))
    filter_phrase = _filter_phrase(applied_filters)
    opening = _pool_opening(count, applied_filters)
    if filter_phrase:
        return f"{opening} We currently have {count} {filter_phrase}."
    return f"{opening} We currently have {count} chocolates to explore."


def select_next_best_attribute(candidate_pool: List[Dict], state: Dict[str, str]) -> str:
    """Pick one high-impact attribute to ask next.

    Impact heuristic:
    - Build buckets for each candidate attribute on the current pool.
    - Estimate split power as (total - largest bucket) with a small diversity bonus.
    """
    if not isinstance(candidate_pool, list):
        candidate_pool = []
    total = len(candidate_pool)

    asked = _asked_attributes(state)
    active = _active_attributes(state)

    candidates = [
        "flavor_direction",
        "intensity",
        "cocoa_percentage",
        "origin",
        "budget",
        "brand_preference",
        "context",
    ]
    candidates = [a for a in candidates if a not in asked and a not in active]
    if not candidates:
        return ""

    if total <= 0:
        # Fallback order when no pool statistics are available.
        return candidates[0]

    scored: List[Tuple[str, float]] = []
    for attr in candidates:
        buckets = _attribute_buckets(candidate_pool, attr)
        if not buckets:
            continue
        largest = max(buckets.values())
        reduction = float(total - largest)
        diversity_bonus = 0.2 * float(max(0, len(buckets) - 1))
        score = reduction + diversity_bonus
        scored.append((attr, score))

    if not scored:
        return candidates[0]

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[0][0]


def generate_sommelier_question(
    attribute: str,
    state: Dict[str, str],
    candidate_count: int,
    applied_filters: Dict[str, str],
    user_message: str = "",
) -> Dict[str, List[str] | str]:
    """Generate one conversational narrowing question."""
    pool_line = describe_candidate_pool(candidate_count, applied_filters)
    ambiguous = _is_ambiguous(user_message)

    if ambiguous:
        question = (
            "If you're unsure, we can explore three directions: fruity and bright, "
            "nutty and caramel-forward, or bold and intense dark. "
            "Which sounds most appealing?"
        )
        return {
            "question": f"{pool_line}\n\n{question}",
            "answer_options": [
                "Fruity & bright",
                "Nutty & caramel-forward",
                "Bold & intense",
                "Show a tasting flight",
            ],
        }

    templates = {
        "flavor_direction": [
            "Would you prefer something fruity and bright, or more nutty and caramel-like?",
            "Shall we go toward a lively fruity profile, or a rounder nutty-caramel direction?",
            "For flavor style, do you lean more fruity and fresh, or nutty and gourmand?",
        ],
        "intensity": [
            "Would you like a bold, intense profile or something smoother and creamier?",
            "Do you prefer a powerful dark structure, or a softer creamy texture?",
            "Should I focus on intense cocoa character, or a smoother melt?",
        ],
        "cocoa_percentage": [
            "Do you have a cocoa percentage in mind, like around 70% or 85%+?",
            "Would a moderate cocoa level suit you, or do you want a high-intensity percentage?",
            "Should we target a specific cocoa range to narrow this further?",
        ],
        "origin": [
            "Shall we narrow by origin next: maker country or cocoa bean origin?",
            "Would you like to filter by chocolatier country, or by bean origin?",
            "Should I focus on production origin, or cocoa terroir origin?",
        ],
        "budget": [
            "Would you like to set a budget range to narrow the list faster?",
            "Do you want to define a price range before I shortlist?",
            "Shall I tailor this by budget band next?",
        ],
        "brand_preference": [
            "Do you want familiar brands, or are you open to discovering niche makers?",
            "Would you rather stay with known brands, or explore new artisan houses?",
            "Should I prioritize trusted labels or discovery picks?",
        ],
        "context": [
            "Is this for everyday enjoyment, or for a gift occasion?",
            "Will this be for personal tasting, or for gifting?",
            "Are you choosing for yourself, or for a special gift moment?",
        ],
        "chocolate_type": [
            "Would you like dark, milk, or white chocolate?",
            "To set the base style, should I focus on dark, milk, or white?",
            "Which type should I center first: dark, milk, or white?",
        ],
    }
    options = {
        "flavor_direction": ["Fruity & bright", "Nutty & caramel-like", "Spicy & bold", "No preference"],
        "intensity": ["Bold / Intense", "Smooth / Creamy", "No preference"],
        "cocoa_percentage": ["Around 60-70%", "Around 70-85%", "85%+", "No preference"],
        "origin": ["Maker country", "Cocoa bean origin", "No preference"],
        "budget": ["Under $10", "$10-$20", "$20-$40", "Premium (>$40)", "No budget limit"],
        "brand_preference": ["Familiar brands", "Open to new makers", "No preference"],
        "context": ["Everyday enjoyment", "Gift", "No preference"],
        "chocolate_type": ["Dark", "Milk", "White", "No preference"],
    }

    variants = templates.get(attribute) or [
        "Would you like to narrow by flavor, intensity, origin, or budget?"
    ]
    signature = int(candidate_count or 0) + len((attribute or "").strip()) + len((user_message or "").strip())
    question = _pick_variant(variants, signature)
    return {
        "question": f"{pool_line}\n\n{question}",
        "answer_options": list(options.get(attribute, [])),
    }


def _is_ambiguous(text: str) -> bool:
    lower = (text or "").strip().lower()
    if not lower:
        return False
    return any(re.search(p, lower) for p in _AMBIGUOUS_PATTERNS)


def _asked_attributes(state: Dict[str, str]) -> set[str]:
    raw = str((state or {}).get("_asked_fields", "") or "").strip()
    if not raw:
        return set()
    return {token.strip() for token in raw.split(",") if token.strip()}


def _active_attributes(state: Dict[str, str]) -> set[str]:
    active = set()
    for field in [
        "chocolate_type",
        "flavor_direction",
        "intensity",
        "cocoa_percentage",
        "origin",
        "budget",
        "brand_preference",
        "context",
    ]:
        value = str((state or {}).get(field, "") or "").strip().lower()
        if value and value not in {"no preference", "any", "whatever", "not sure"}:
            active.add(field)
    return active


def _attribute_buckets(candidate_pool: List[Dict], attribute: str) -> Counter:
    extractor = {
        "flavor_direction": _extract_flavor_bucket,
        "intensity": _extract_intensity_bucket,
        "cocoa_percentage": _extract_cocoa_bucket,
        "origin": _extract_origin_bucket,
        "budget": _extract_budget_bucket,
        "brand_preference": _extract_brand_bucket,
        "context": _extract_context_bucket,
        "chocolate_type": _extract_type_bucket,
    }.get(attribute)
    if not extractor:
        return Counter()

    values = []
    for product in candidate_pool:
        val = extractor(product or {})
        if val and val != "unknown":
            values.append(val)
    return Counter(values)


def _filter_phrase(applied_filters: Dict[str, str]) -> str:
    data = {k: str(v).strip() for k, v in (applied_filters or {}).items() if str(v).strip()}
    choc_type = data.get("chocolate_type", "")
    flavor = data.get("flavor_direction", "")
    origin = data.get("origin", "")
    budget = data.get("budget", "")
    context = data.get("context", "")

    flavor_tokens = _normalize_descriptor_tokens(flavor)
    choc_type_token = choc_type.strip().lower()
    if choc_type_token:
        flavor_tokens = [token for token in flavor_tokens if token != choc_type_token]

    if choc_type_token and flavor_tokens:
        base = f"{' / '.join(flavor_tokens)} {choc_type_token} chocolates"
    elif choc_type_token:
        base = f"{choc_type_token} chocolates"
    elif flavor_tokens:
        base = f"{' / '.join(flavor_tokens)} chocolates"
    else:
        base = "chocolates"

    tails: List[str] = []
    if origin:
        tails.append(f"from {origin}")
    if budget and budget.lower() not in {"no budget limit"}:
        tails.append(f"within {budget}")
    if context.lower() == "gift":
        tails.append("for gifts")
    elif context.lower() == "everyday":
        tails.append("for everyday tasting")

    if tails:
        return f"{base} {' and '.join(tails)}"
    return base


def _pool_opening(candidate_count: int, applied_filters: Dict[str, str]) -> str:
    if candidate_count > 1200:
        options = [
            "Let's narrow this down step by step.",
            "We're starting from a broad cellar.",
            "Plenty of room to refine this selection.",
        ]
    elif candidate_count > 300:
        options = [
            "Good direction.",
            "Nice, we're getting more focused.",
            "Great, this is a workable set.",
        ]
    elif candidate_count > 80:
        options = [
            "Now we're in a tighter range.",
            "We're getting close to a strong shortlist.",
            "This is already a more focused lineup.",
        ]
    else:
        options = [
            "Excellent, this is a compact shortlist.",
            "Great, we now have a very focused set.",
            "Perfect, this pool is now quite selective.",
        ]

    signature = candidate_count + sum(ord(ch) for ch in "|".join(f"{k}:{v}" for k, v in sorted((applied_filters or {}).items())))
    return options[signature % len(options)]


def _normalize_descriptor_tokens(value: str) -> List[str]:
    raw = (value or "").strip().lower()
    if not raw:
        return []
    tokens = [token.strip() for token in re.split(r"[,/|]", raw) if token.strip()]
    cleaned: List[str] = []
    for token in tokens:
        token = re.sub(r"\s+", " ", token)
        if token and token not in cleaned:
            cleaned.append(token)
    return cleaned


def _pick_variant(variants: List[str], signature: int) -> str:
    if not variants:
        return ""
    idx = abs(int(signature)) % len(variants)
    return variants[idx]


def _extract_flavor_bucket(product: Dict) -> str:
    blob = " ".join(
        [
            str(product.get("flavor_notes_primary", "")),
            str(product.get("flavor_notes_secondary", "")),
            str(product.get("tasting_notes", "")),
            str(product.get("name", "")),
        ]
    ).lower()
    if any(k in blob for k in ["fruit", "berry", "citrus", "fig", "apricot", "raisin", "plum", "peach"]):
        return "fruity"
    if any(k in blob for k in ["nut", "hazelnut", "almond", "praline", "caramel", "toffee"]):
        return "nutty_caramel"
    if any(k in blob for k in ["spice", "pepper", "chili", "smoke"]):
        return "spicy_bold"
    return "classic"


def _extract_intensity_bucket(product: Dict) -> str:
    cocoa = _as_float(product.get("cocoa_percentage"))
    if cocoa is None:
        return "unknown"
    if cocoa >= 80:
        return "very_intense"
    if cocoa >= 70:
        return "intense"
    if cocoa >= 55:
        return "balanced"
    return "smooth"


def _extract_cocoa_bucket(product: Dict) -> str:
    cocoa = _as_float(product.get("cocoa_percentage"))
    if cocoa is None:
        return "unknown"
    if cocoa < 60:
        return "under_60"
    if cocoa < 75:
        return "60_74"
    if cocoa < 85:
        return "75_84"
    return "85_plus"


def _extract_origin_bucket(product: Dict) -> str:
    maker = str(product.get("maker_country", "") or "").strip()
    origin = str(product.get("origin_country", "") or "").strip()
    if maker:
        return f"maker:{maker}"
    if origin:
        return f"bean:{origin}"
    return "unknown"


def _extract_budget_bucket(product: Dict) -> str:
    price = _as_float(product.get("price_retail"))
    if price is None:
        return "unknown"
    if price < 10:
        return "under_10"
    if price < 20:
        return "10_19"
    if price < 40:
        return "20_39"
    return "40_plus"


def _extract_brand_bucket(product: Dict) -> str:
    brand = str(product.get("brand", "") or "").strip()
    return brand if brand else "unknown"


def _extract_context_bucket(_product: Dict) -> str:
    # Context is user-side (gift vs everyday), not product metadata.
    return "unknown"


def _extract_type_bucket(product: Dict) -> str:
    p_type = str(product.get("type", "") or "").lower()
    cocoa = _as_float(product.get("cocoa_percentage"))
    if "dark" in p_type:
        return "dark"
    if "milk" in p_type:
        return "milk"
    if "white" in p_type:
        return "white"
    if cocoa is None:
        return "unknown"
    if cocoa >= 70:
        return "dark"
    if cocoa <= 40:
        return "white"
    return "milk"


def _as_float(value) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)", str(value or ""))
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None
