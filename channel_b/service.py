import json
import os
from pathlib import Path

import numpy as np
import psycopg2
from sentence_transformers import SentenceTransformer

from channel_a.normalization.normalize import normalize_country_from_query

class ChannelBService:
    def __init__(self, embeddings_path: str, products_path: str = "data/chocolates.json"):
        self.model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
        self.db_url = os.getenv("DATABASE_URL")

        if not self.db_url:
            # Fallback to JSON in-memory search
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

        if self.db_url:
            return self._rank_sql(candidate_ids, semantic_query, top_k, min_score)
        else:
            return self._rank_json(candidate_ids, semantic_query, top_k, min_score)

    def _rank_sql(self, candidate_ids: list[int], semantic_query: str, top_k: int, min_score: float) -> list[int]:
        """Vector search using pgvector."""
        try:
            query_vec = self.model.encode(semantic_query, normalize_embeddings=True).tolist()
            
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            
            # Use cosine similarity <=> 1 - (vec1 . vec2)
            # score = 1 - (query_vec <=> embedding)
            cur.execute("""
                SELECT id, 1 - (embedding <=> %s::vector) as score
                FROM chocolates
                WHERE id = ANY(%s)
                AND (1 - (embedding <=> %s::vector)) >= %s
                ORDER BY score DESC
                LIMIT %s;
            """, (query_vec, candidate_ids, query_vec, min_score, top_k))
            
            results = [r[0] for r in cur.fetchall()]
            cur.close()
            conn.close()
            return results
        except Exception as e:
            print(f"SQL Rank Error: {e}")
            return self._rank_json(candidate_ids, semantic_query, top_k, min_score)

    def _rank_json(self, candidate_ids: list[int], semantic_query: str, top_k: int, min_score: float) -> list[int]:
        # maker_country hard filter (Channel B)
        country = normalize_country_from_query(semantic_query)
        if country and hasattr(self, 'id_to_maker_country') and self.id_to_maker_country:
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
            if not hasattr(self, 'id_to_vector'):
                continue
            vec = self.id_to_vector.get(pid)
            if vec is None:
                continue
            score = float(np.dot(query_vec, vec))
            scored.append((pid, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Filter by threshold
        final_results = [pid for pid, score in scored if score >= min_score]
        
        return final_results[:top_k]
