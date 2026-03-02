import re
from statistics import pvariance
from typing import Dict, List, Optional, Set, Tuple


UNKNOWN_METADATA_PENALTY = 0.35


class RecommenderService:
    def __init__(self, channel_a_service, channel_b_service, explainer=None):
        self.channel_a = channel_a_service
        self.channel_b = channel_b_service
        self.explainer = explainer
        self.product_by_id: Dict[int, dict] = {}
        self.brand_frequency: Dict[str, int] = {}
        self._build_product_lookup()

    def recommend(
        self,
        query: str,
        top_k: int = 10,
        segment: Optional[str] = None,
        state: Optional[dict] = None,
        hard_filters: Optional[dict] = None,
    ):
        # 1) Eligibility + deterministic hard filtering with unknown-tolerant penalties.
        candidate_ids = self.channel_a.run(query)
        candidate_ids, soft_penalties, relaxed_by_filter = self._apply_dynamic_hard_filters(
            candidate_ids,
            hard_filters,
        )

        if not candidate_ids:
            return {
                "candidates": [],
                "ranked": [],
                "semantic_scores": [],
                "max_similarity": 0.0,
                "similarity_variance": 0.0,
                "explanation": "No products satisfy hard constraints",
                "reason": "No products satisfy hard constraints",
                "explanation_layer": {
                    "matched_preferences": [],
                    "relaxed_preferences": sorted(relaxed_by_filter),
                    "tradeoff": "Constraints are too strict for current data.",
                },
            }

        # 2) Semantic remainder
        semantic_query = self._extract_semantic_query(query)

        # 3) Semantic ranking with scores (FAISS/pgvector path preserved)
        scored = self.channel_b.rank_with_scores(
            candidate_ids=candidate_ids,
            semantic_query=semantic_query,
            top_k=max(top_k, 25),
            min_score=0.35,
        )
        if not scored:
            return {
                "candidates": candidate_ids,
                "ranked": [],
                "semantic_scores": [],
                "max_similarity": 0.0,
                "similarity_variance": 0.0,
                "reason": "No semantic matches above threshold",
                "explanation_layer": {
                    "matched_preferences": [],
                    "relaxed_preferences": sorted(relaxed_by_filter),
                    "tradeoff": "Semantic similarity is too low for a confident recommendation.",
                },
            }

        semantic_ranked_ids = [pid for pid, _ in scored]

        # 4) Segment-aware rerank + unknown metadata soft penalties.
        ranked_ids = self._segment_weighted_rerank(
            ranked_ids=semantic_ranked_ids,
            segment=segment,
            state=state,
            top_k=max(top_k, 25),
            soft_penalties=soft_penalties,
        )

        # 5) Diversity post-rerank: brand/origin caps and flavor-profile variety.
        ranked_ids = self._diversify_ranked_ids(ranked_ids, top_k=top_k)

        score_map = {pid: score for pid, score in scored}
        ranked_scores = [float(score_map.get(pid, 0.0)) for pid in ranked_ids]
        max_similarity = max(ranked_scores) if ranked_scores else 0.0
        similarity_variance = pvariance(ranked_scores) if len(ranked_scores) > 1 else 0.0

        explanation_layer = self._build_explanation_layer(
            ranked_ids=ranked_ids,
            state=state,
            hard_filters=hard_filters,
            relaxed_by_filter=relaxed_by_filter,
        )

        return {
            "candidates": candidate_ids,
            "ranked": ranked_ids,
            "semantic_scores": [{"id": pid, "score": float(score_map.get(pid, 0.0))} for pid in ranked_ids],
            "max_similarity": float(max_similarity),
            "similarity_variance": float(similarity_variance),
            "explanation_layer": explanation_layer,
        }

    def estimate_candidate_count(self, query: str, hard_filters: Optional[dict] = None) -> int:
        candidate_ids = self.channel_a.run(query)
        candidate_ids, _, _ = self._apply_dynamic_hard_filters(candidate_ids, hard_filters)
        return len(candidate_ids)

    def build_tasting_flight(self, ranked_ids: List[int], size: int = 3) -> List[int]:
        if not ranked_ids:
            return []

        selected: List[int] = []
        seen_profiles: Set[str] = set()

        for pid in ranked_ids:
            profile = self._flavor_profile_from_product(self.product_by_id.get(pid, {}))
            if profile in seen_profiles:
                continue
            selected.append(pid)
            seen_profiles.add(profile)
            if len(selected) >= size:
                return selected

        for pid in ranked_ids:
            if pid in selected:
                continue
            selected.append(pid)
            if len(selected) >= size:
                break

        return selected

    def _extract_semantic_query(self, query: str) -> str:
        stop_words = ["vegan", "dark", "milk", "white", "under", "below", "allergen", "nut free"]
        q = query.lower()
        for word in stop_words:
            q = q.replace(word, "")
        return q.strip() or query

    def _build_product_lookup(self):
        chocolates = getattr(getattr(self.channel_a, "index", None), "chocolates", [])
        for product in chocolates:
            pid = product.get("id")
            if pid is None:
                continue
            pid_int = int(pid)
            self.product_by_id[pid_int] = product

            brand = str(product.get("brand", "")).strip().lower()
            if brand:
                self.brand_frequency[brand] = self.brand_frequency.get(brand, 0) + 1

    def _apply_dynamic_hard_filters(
        self,
        candidate_ids: List[int],
        hard_filters: Optional[dict],
    ) -> Tuple[List[int], Dict[int, float], Set[str]]:
        if not candidate_ids or not hard_filters:
            return candidate_ids, {}, set()

        normalized_filters = {
            key: ("" if value is None else str(value).strip().lower())
            for key, value in hard_filters.items()
        }

        filtered: List[int] = []
        penalties: Dict[int, float] = {}
        relaxed_preferences: Set[str] = set()

        for pid in candidate_ids:
            product = self.product_by_id.get(pid, {})
            if not product:
                continue

            penalty = 0.0
            rejected = False

            origin = normalized_filters.get("origin", "")
            if origin:
                status = self._origin_match_status(
                    product,
                    origin,
                    normalized_filters.get("origin_scope", ""),
                )
                if status == "mismatch":
                    rejected = True
                elif status == "unknown":
                    penalty += UNKNOWN_METADATA_PENALTY
                    relaxed_preferences.add("origin")

            choc_type = normalized_filters.get("chocolate_type", "")
            if not rejected and choc_type:
                status = self._type_match_status(product, choc_type)
                if status == "mismatch":
                    rejected = True
                elif status == "unknown":
                    penalty += UNKNOWN_METADATA_PENALTY
                    relaxed_preferences.add("chocolate_type")

            budget = normalized_filters.get("budget", "")
            if not rejected and budget:
                status = self._budget_match_status(product, budget)
                if status == "mismatch":
                    rejected = True
                elif status == "unknown":
                    penalty += UNKNOWN_METADATA_PENALTY
                    relaxed_preferences.add("budget")

            dietary = normalized_filters.get("dietary", "")
            if not rejected and dietary:
                status = self._dietary_match_status(product, dietary)
                if status == "mismatch":
                    rejected = True
                elif status == "unknown":
                    penalty += UNKNOWN_METADATA_PENALTY
                    relaxed_preferences.add("dietary")

            cert = normalized_filters.get("certification", "")
            if not rejected and cert:
                status = self._certification_match_status(product, cert)
                if status == "mismatch":
                    rejected = True
                elif status == "unknown":
                    penalty += UNKNOWN_METADATA_PENALTY
                    relaxed_preferences.add("certification")

            if rejected:
                continue

            filtered.append(pid)
            if penalty > 0.0:
                penalties[pid] = penalty

        return filtered, penalties, relaxed_preferences

    def _segment_weighted_rerank(
        self,
        ranked_ids: List[int],
        segment: Optional[str],
        state: Optional[dict],
        top_k: int,
        soft_penalties: Optional[Dict[int, float]] = None,
    ) -> List[int]:
        if not ranked_ids:
            return []

        normalized_state = {
            k: ("" if v is None else str(v).strip().lower())
            for k, v in (state or {}).items()
        }

        scored = []
        total = len(ranked_ids)
        penalty_map = soft_penalties or {}

        for idx, pid in enumerate(ranked_ids):
            base_score = float(total - idx)
            product = self.product_by_id.get(pid, {})
            boost = self._segment_boost(segment or "", normalized_state, product)
            penalty = float(penalty_map.get(pid, 0.0))
            scored.append((pid, base_score + boost - penalty))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [pid for pid, _ in scored[:top_k]]

    def _diversify_ranked_ids(self, ranked_ids: List[int], top_k: int) -> List[int]:
        if not ranked_ids:
            return []

        selected: List[int] = []
        brand_counts: Dict[str, int] = {}
        origin_counts: Dict[str, int] = {}

        def can_add(pid: int) -> bool:
            product = self.product_by_id.get(pid, {})
            brand = self._norm_brand(product)
            origin = self._norm_origin(product)
            if brand and brand_counts.get(brand, 0) >= 2:
                return False
            if origin and origin_counts.get(origin, 0) >= 2:
                return False
            return True

        def add(pid: int) -> None:
            product = self.product_by_id.get(pid, {})
            selected.append(pid)
            brand = self._norm_brand(product)
            origin = self._norm_origin(product)
            if brand:
                brand_counts[brand] = brand_counts.get(brand, 0) + 1
            if origin:
                origin_counts[origin] = origin_counts.get(origin, 0) + 1

        # Pass 1: pick strongest valid item.
        for pid in ranked_ids:
            if can_add(pid):
                add(pid)
                break

        # Pass 2: try to guarantee a second flavor profile in the top set.
        if selected and top_k >= 2:
            first_profile = self._flavor_profile_from_product(self.product_by_id.get(selected[0], {}))
            for pid in ranked_ids:
                if pid in selected or not can_add(pid):
                    continue
                profile = self._flavor_profile_from_product(self.product_by_id.get(pid, {}))
                if profile != first_profile:
                    add(pid)
                    break

        # Pass 3: fill remaining slots with cap constraints.
        for pid in ranked_ids:
            if len(selected) >= top_k:
                break
            if pid in selected:
                continue
            if can_add(pid):
                add(pid)

        return selected

    def _segment_boost(self, segment: str, state: Dict[str, str], product: dict) -> float:
        if segment == "Rational Health-Conscious":
            return self._health_boost(state, product)
        if segment == "Impulsive-Involved":
            return self._impulsive_boost(state, product)
        if segment == "Uninvolved":
            return self._uninvolved_boost(state, product)
        return 0.0

    def _health_boost(self, state: Dict[str, str], product: dict) -> float:
        score = 0.0
        blob = self._product_blob(product)

        cert_pref = state.get("certification", "")
        if cert_pref and cert_pref != "not required":
            cert_tokens = ["organic", "fair trade", "fairtrade", "sustainab", "ethical", "direct trade"]
            if any(token in cert_pref for token in cert_tokens):
                for token in cert_tokens:
                    if token in cert_pref and token in blob:
                        score += 0.8
            elif any(token in blob for token in cert_tokens):
                score += 0.6

        dietary_pref = state.get("dietary", "")
        if dietary_pref:
            for token in [t.strip() for t in dietary_pref.split(",") if t.strip()]:
                if token in blob:
                    score += 0.6

        cocoa_pref = state.get("cocoa_percentage", "")
        target = self._first_number(cocoa_pref)
        cocoa_val = self._first_number(str(product.get("cocoa_percentage", "")))
        if target is not None and cocoa_val is not None:
            delta = abs(target - cocoa_val)
            if delta <= 5:
                score += 0.6
            elif delta <= 10:
                score += 0.3

        return score

    def _impulsive_boost(self, state: Dict[str, str], product: dict) -> float:
        score = 0.0
        flavor_blob = " ".join(
            [
                str(product.get("flavor_notes_primary", "")),
                str(product.get("flavor_notes_secondary", "")),
                str(product.get("tasting_notes", "")),
                str(product.get("name", "")),
            ]
        ).lower()

        flavor_pref = state.get("flavor_direction", "") or state.get("taste", "")
        if flavor_pref:
            for flavor in [t.strip() for t in flavor_pref.split(",") if t.strip()]:
                if flavor in flavor_blob:
                    score += 0.7

        type_pref = state.get("chocolate_type", "")
        cocoa_val = self._first_number(str(product.get("cocoa_percentage", "")))
        if type_pref == "dark" and cocoa_val is not None and cocoa_val >= 70:
            score += 0.8
        if type_pref == "milk" and cocoa_val is not None and 30 <= cocoa_val <= 65:
            score += 0.8
        if type_pref == "white" and cocoa_val is not None and cocoa_val <= 40:
            score += 0.8

        intensity = state.get("intensity", "")
        if intensity == "intense" and cocoa_val is not None and cocoa_val >= 75:
            score += 0.7
        if intensity == "smooth" and cocoa_val is not None and cocoa_val <= 65:
            score += 0.7

        if state.get("context") == "gift":
            rating = self._first_number(str(product.get("rating", "")))
            if rating is not None and rating >= 4.0:
                score += 0.2

        return score

    def _uninvolved_boost(self, state: Dict[str, str], product: dict) -> float:
        score = 0.0

        budget_cap = self._budget_cap(state.get("budget", ""))
        price = self._first_number(str(product.get("price_retail", "")))
        if budget_cap is not None and price is not None:
            if price <= budget_cap:
                score += 1.0
            else:
                score -= 1.0

        brand_pref = state.get("brand_preference", "")
        brand = str(product.get("brand", "")).strip().lower()
        freq = self.brand_frequency.get(brand, 0)
        if brand_pref == "familiar" and freq >= 8:
            score += 0.6
        if brand_pref == "open" and 0 < freq <= 3:
            score += 0.6

        if state.get("context") == "gift":
            rating = self._first_number(str(product.get("rating", "")))
            if rating is not None and rating >= 4.0:
                score += 0.2

        return score

    def _type_match_status(self, product: dict, target_type: str) -> str:
        target = target_type.strip().lower()
        product_type = str(product.get("type", "")).strip().lower()
        cocoa_val = self._first_number(str(product.get("cocoa_percentage", "")))

        if not product_type and cocoa_val is None:
            return "unknown"

        if target == "dark":
            return "match" if ("dark" in product_type or (cocoa_val is not None and cocoa_val >= 70)) else "mismatch"
        if target == "milk":
            return "match" if ("milk" in product_type or (cocoa_val is not None and 30 <= cocoa_val <= 65)) else "mismatch"
        if target == "white":
            return "match" if ("white" in product_type or (cocoa_val is not None and cocoa_val <= 40)) else "mismatch"
        return "match"

    def _origin_match_status(self, product: dict, target_origin: str, scope: str = "") -> str:
        target = self._canonical_country(target_origin)
        maker_country = self._canonical_country(str(product.get("maker_country", "")))
        origin_country = self._canonical_country(str(product.get("origin_country", "")))

        normalized_scope = str(scope or "").strip().lower()

        if normalized_scope == "maker_country":
            if not maker_country:
                return "unknown"
            return "match" if target and maker_country == target else "mismatch"

        if normalized_scope == "origin_country":
            if not origin_country:
                return "unknown"
            return "match" if target and origin_country == target else "mismatch"

        if not maker_country and not origin_country:
            return "unknown"

        # "from France" can mean maker location or bean origin.
        if target and target in {maker_country, origin_country}:
            return "match"
        return "mismatch"

    def _budget_match_status(self, product: dict, budget_text: str) -> str:
        price = self._first_number(str(product.get("price_retail", "")))
        if price is None:
            return "unknown"

        min_budget, max_budget = self._budget_bounds(budget_text)
        if min_budget is not None and price < min_budget:
            return "mismatch"
        if max_budget is not None and price > max_budget:
            return "mismatch"
        return "match"

    def _dietary_match_status(self, product: dict, dietary_text: str) -> str:
        requested = [token.strip() for token in dietary_text.split(",") if token.strip()]
        if not requested:
            return "match"

        blob = self._product_blob(product)
        if not blob.strip():
            return "unknown"

        tag_aliases = {
            "vegan": ["vegan"],
            "low sugar": ["low sugar", "sugar-free", "sugar free"],
            "dairy-free": ["dairy-free", "dairy free", "no milk"],
            "gluten-free": ["gluten-free", "gluten free"],
            "keto": ["keto"],
        }

        unknown = False
        for tag in requested:
            aliases = tag_aliases.get(tag, [tag])
            if any(alias in blob for alias in aliases):
                continue

            if tag == "vegan" and any(bad in blob for bad in ["contains milk", "milk powder", "dairy"]):
                return "mismatch"
            if tag == "dairy-free" and any(bad in blob for bad in ["contains milk", "milk powder"]):
                return "mismatch"

            unknown = True

        return "unknown" if unknown else "match"

    def _certification_match_status(self, product: dict, certification_text: str) -> str:
        if not certification_text or certification_text == "not required":
            return "match"

        blob = self._product_blob(product)
        if not blob.strip():
            return "unknown"

        requested = [token.strip() for token in certification_text.split(",") if token.strip()]
        if not requested:
            return "match"

        cert_aliases = {
            "organic": ["organic"],
            "fair trade": ["fair trade", "fairtrade", "direct trade"],
            "sustainability": ["sustainable", "sustainability", "ethical"],
            "ethical sourcing": ["ethical", "sustainable"],
            "important": ["organic", "fair trade", "fairtrade", "sustainable", "ethical"],
        }

        unknown = False
        for tag in requested:
            aliases = cert_aliases.get(tag, [tag])
            if any(alias in blob for alias in aliases):
                continue
            unknown = True

        return "unknown" if unknown else "match"

    def _build_explanation_layer(
        self,
        ranked_ids: List[int],
        state: Optional[dict],
        hard_filters: Optional[dict],
        relaxed_by_filter: Set[str],
    ) -> Dict[str, object]:
        normalized_state = {
            k: ("" if v is None else str(v).strip().lower())
            for k, v in (state or {}).items()
        }
        hard = {
            k: ("" if v is None else str(v).strip().lower())
            for k, v in (hard_filters or {}).items()
        }

        active_fields = []
        for field in [
            "origin",
            "chocolate_type",
            "budget",
            "dietary",
            "certification",
            "flavor_direction",
            "intensity",
            "brand_preference",
        ]:
            if hard.get(field) or normalized_state.get(field):
                active_fields.append(field)

        matched: List[str] = []
        relaxed: Set[str] = set(relaxed_by_filter)

        top_ids = ranked_ids[:5]
        for field in active_fields:
            value = hard.get(field) or normalized_state.get(field)
            if not value:
                continue
            statuses = [self._field_status(field, self.product_by_id.get(pid, {}), value) for pid in top_ids]
            if any(status == "match" for status in statuses):
                matched.append(field)
            elif any(status == "unknown" for status in statuses):
                relaxed.add(field)
            else:
                relaxed.add(field)

        tradeoff = (
            "Some preferences were relaxed because metadata was missing or ambiguous; results were ranked by closest fit."
            if relaxed
            else "All stated preferences were matched directly in the top results."
        )

        return {
            "matched_preferences": sorted(set(matched)),
            "relaxed_preferences": sorted(relaxed),
            "tradeoff": tradeoff,
        }

    def _field_status(self, field: str, product: dict, value: str) -> str:
        if field == "origin":
            return self._origin_match_status(product, value)
        if field == "chocolate_type":
            return self._type_match_status(product, value)
        if field == "budget":
            return self._budget_match_status(product, value)
        if field == "dietary":
            return self._dietary_match_status(product, value)
        if field == "certification":
            return self._certification_match_status(product, value)
        if field == "flavor_direction":
            blob = self._flavor_blob(product)
            values = [token.strip() for token in value.split(",") if token.strip()]
            if not blob.strip():
                return "unknown"
            return "match" if any(token in blob for token in values) else "unknown"
        if field == "intensity":
            cocoa = self._first_number(str(product.get("cocoa_percentage", "")))
            if cocoa is None:
                return "unknown"
            if value == "intense":
                return "match" if cocoa >= 75 else "mismatch"
            if value == "smooth":
                return "match" if cocoa <= 65 else "mismatch"
            return "unknown"
        if field == "brand_preference":
            brand = self._norm_brand(product)
            if not brand:
                return "unknown"
            freq = self.brand_frequency.get(brand, 0)
            if value == "familiar":
                return "match" if freq >= 8 else "unknown"
            if value == "open":
                return "match" if 0 < freq <= 3 else "unknown"
            return "unknown"
        return "unknown"

    def _budget_bounds(self, text: str) -> Tuple[Optional[float], Optional[float]]:
        if not text:
            return (None, None)

        lower = text.lower()
        range_match = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)", lower)
        if range_match:
            return (float(range_match.group(1)), float(range_match.group(2)))

        under_match = re.search(r"(?:under|below|max)\s*\$?\s*(\d+(?:\.\d+)?)", lower)
        if under_match:
            return (None, float(under_match.group(1)))

        over_match = re.search(r"(?:over|above|at least|more than)\s*\$?\s*(\d+(?:\.\d+)?)", lower)
        if over_match:
            return (float(over_match.group(1)), None)

        around_match = re.search(r"(?:around)\s*\$?\s*(\d+(?:\.\d+)?)", lower)
        if around_match:
            center = float(around_match.group(1))
            return (max(0.0, center - 5.0), center + 5.0)

        if "budget-friendly" in lower or "cheap" in lower:
            return (None, 10.0)
        if "premium" in lower or "luxury" in lower or "expensive" in lower:
            return (15.0, None)

        exact = self._first_number(lower)
        if exact is not None:
            return (None, exact)

        return (None, None)

    def _budget_cap(self, text: str) -> Optional[float]:
        _, max_budget = self._budget_bounds(text)
        return max_budget

    def _product_blob(self, product: dict) -> str:
        fields = [
            "dietary",
            "maker_philosophy",
            "ingredients",
            "awards",
            "expert_review",
            "flavor_notes_primary",
            "flavor_notes_secondary",
            "tasting_notes",
            "name",
            "description",
        ]
        parts = []
        for field in fields:
            value = product.get(field)
            if value in (None, ""):
                parts.append("unknown")
            else:
                parts.append(str(value))
        return " ".join(parts).lower()

    def _flavor_blob(self, product: dict) -> str:
        return " ".join(
            [
                str(product.get("flavor_notes_primary", "")),
                str(product.get("flavor_notes_secondary", "")),
                str(product.get("tasting_notes", "")),
            ]
        ).lower()

    def _flavor_profile_from_product(self, product: dict) -> str:
        blob = self._flavor_blob(product)
        profile_map = {
            "fruity": ["fruit", "berry", "citrus", "plum", "peach"],
            "nutty": ["nut", "hazelnut", "almond", "praline"],
            "spicy": ["spice", "pepper", "chili", "cinnamon"],
            "caramel": ["caramel", "toffee", "honey"],
            "floral": ["floral", "jasmine", "rose", "lavender"],
            "earthy": ["earth", "wood", "smoke", "malt"],
            "creamy": ["cream", "milk", "butter"],
        }
        for label, tokens in profile_map.items():
            if any(token in blob for token in tokens):
                return label
        return "classic"

    def _norm_brand(self, product: dict) -> str:
        return str(product.get("brand", "")).strip().lower()

    def _norm_origin(self, product: dict) -> str:
        origin = str(product.get("origin_country", "")).strip().lower()
        if origin:
            return origin
        return str(product.get("maker_country", "")).strip().lower()

    def _canonical_country(self, value: str) -> str:
        text = re.sub(r"\s+", " ", str(value or "").strip().lower())
        if not text:
            return ""

        aliases = {
            "u.s.a": "usa",
            "u.s": "usa",
            "united states": "usa",
            "america": "usa",
            "american": "usa",
            "french": "france",
            "italian": "italy",
            "belgian": "belgium",
            "swiss": "switzerland",
            "japanese": "japan",
            "spanish": "spain",
            "german": "germany",
            "canadian": "canada",
            "brazilian": "brazil",
            "united kingdom": "uk",
            "britain": "uk",
            "great britain": "uk",
            "england": "uk",
        }
        return aliases.get(text, text)

    def _first_number(self, text: str) -> Optional[float]:
        match = re.search(r"(\d+(?:\.\d+)?)", str(text))
        if not match:
            return None
        return float(match.group(1))
