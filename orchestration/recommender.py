class RecommenderService:
    def __init__(self, channel_a_service, channel_b_service, explainer=None):
        self.channel_a = channel_a_service
        self.channel_b = channel_b_service
        self.explainer = explainer
    
    def recommend(self, query: str, top_k: int = 10):
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
            top_k=top_k
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
