import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from channel_a.normalization.normalize import normalize_country_from_query


class ChannelBService:
    def __init__(self, embeddings_path: str, products_path: str = "data/chocolates.json"):
        self.model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")

        with open(embeddings_path, "r", encoding="utf-8") as f:
            records = json.load(f)

        # id -> vector
        self.id_to_vector = {
            int(r["id"]): np.array(r["embedding"], dtype=np.float32)
            for r in records
        }

        # id -> maker_country
        self.id_to_maker_country = {}
        try:
            p = Path(products_path)
            if p.exists():
                with p.open("r", encoding="utf-8") as pf:
                    products = json.load(pf)

                for prod in products:
                    pid = prod.get("id")
                    country = prod.get("maker_country")
                    if pid is None or not country:
                        continue
                    self.id_to_maker_country[int(pid)] = country
        except Exception:
            self.id_to_maker_country = {}

    def rank(self, candidate_ids: list[int], semantic_query: str, top_k: int, min_score: float = 0.35) -> list[int]:
        if not candidate_ids:
            return []

        # maker_country hard filter (Channel B)
        country = normalize_country_from_query(semantic_query)
        if country and self.id_to_maker_country:
            candidate_ids = [
                pid for pid in candidate_ids
                if self.id_to_maker_country.get(pid) == country
            ]
            if not candidate_ids:
                return []

        if not semantic_query.strip():
            return candidate_ids[:top_k]

        query_vec = self.model.encode(semantic_query, normalize_embeddings=True)

        scored = []
        for pid in candidate_ids:
            vec = self.id_to_vector.get(pid)
            if vec is None:
                continue
            score = float(np.dot(query_vec, vec))
            scored.append((pid, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Filter by threshold
        final_results = [pid for pid, score in scored if score >= min_score]
        
        return final_results[:top_k]