import re
from typing import Dict, List, Optional


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
    ):
        # 1. Eligibility
        candidate_ids = self.channel_a.run(query)
        
        if not candidate_ids:
            return {
                "candidates": [],
                "ranked": [],
                "explanation": "No products satisfy hard constraints",
                "reason": "No products satisfy hard constraints"
            }
        
        # 2. Semantic remainder
        semantic_query = self._extract_semantic_query(query)
        
        # 3. Ranking
        ranked_ids = self.channel_b.rank(
            candidate_ids=candidate_ids,
            semantic_query=semantic_query,
            top_k=top_k,
            min_score=0.35
        )

        # Segment-aware lightweight rerank on top of semantic rank.
        # This preserves Channel B retrieval behavior while biasing toward
        # segment priorities (health/taste/value) for final ordering.
        ranked_ids = self._segment_weighted_rerank(
            ranked_ids=ranked_ids,
            segment=segment,
            state=state,
            top_k=top_k,
        )
        
        return {
            "candidates": candidate_ids,
            "ranked": ranked_ids
        }
    
    def _extract_semantic_query(self, query: str) -> str:
        # Simple stop word removal
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

    def _segment_weighted_rerank(
        self,
        ranked_ids: List[int],
        segment: Optional[str],
        state: Optional[dict],
        top_k: int,
    ) -> List[int]:
        if not ranked_ids:
            return []
        if not segment:
            return ranked_ids[:top_k]

        normalized_state = {
            k: ("" if v is None else str(v).strip().lower())
            for k, v in (state or {}).items()
        }

        scored = []
        total = len(ranked_ids)
        for idx, pid in enumerate(ranked_ids):
            base_score = float(total - idx)
            product = self.product_by_id.get(pid, {})
            boost = self._segment_boost(segment, normalized_state, product)
            scored.append((pid, base_score + boost))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [pid for pid, _ in scored[:top_k]]

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

        taste_pref = state.get("taste", "")
        if taste_pref:
            for taste in [t.strip() for t in taste_pref.split(",") if t.strip()]:
                if taste in flavor_blob:
                    score += 0.7

        intensity = state.get("intensity", "")
        cocoa_val = self._first_number(str(product.get("cocoa_percentage", "")))
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

    def _budget_cap(self, text: str) -> Optional[float]:
        if not text:
            return None
        text = text.lower()

        range_match = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)", text)
        if range_match:
            return float(range_match.group(2))

        under_match = re.search(r"(?:under|below|max)\s*\$?\s*(\d+(?:\.\d+)?)", text)
        if under_match:
            return float(under_match.group(1))

        exact = self._first_number(text)
        if exact is not None:
            return exact

        if "budget-friendly" in text or "cheap" in text:
            return 10.0
        return None

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
        ]
        return " ".join(str(product.get(field, "")) for field in fields).lower()

    def _first_number(self, text: str) -> Optional[float]:
        match = re.search(r"(\d+(?:\.\d+)?)", str(text))
        if not match:
            return None
        return float(match.group(1))
