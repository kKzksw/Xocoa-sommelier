# channel_b/ranking/scorer.py

import torch
from sentence_transformers import util
from typing import List
import pandas as pd

class ChannelBScorer:
    """
    Channel B ranking logic:
    - Receives candidate embeddings and query embedding
    - Computes similarity
    - Returns top_k candidate IDs
    """

    def __init__(self):
        pass  # no state needed for now

    @staticmethod
    def rank_candidates(
        df_candidates: pd.DataFrame,
        candidate_embeddings: torch.Tensor,
        query_embedding: torch.Tensor,
        top_k: int = 5
    ) -> List[int]:
        """
        Rank candidates by similarity to the query.

        Args:
            df_candidates: DataFrame of candidate products (must include 'id' column)
            candidate_embeddings: torch.Tensor of embeddings for candidates
            query_embedding: torch.Tensor of the query embedding
            top_k: number of top results to return

        Returns:
            List[int]: ordered list of candidate IDs (top_k)
        """
        if df_candidates.empty:
            return []

        # Compute cosine similarity
        cos_scores = util.pytorch_cos_sim(query_embedding, candidate_embeddings).squeeze(0)

        # Get top-k indices
        top_scores, top_indices = torch.topk(cos_scores, k=min(top_k, len(df_candidates)))

        # Map back to candidate IDs
        ranked_ids = df_candidates.iloc[top_indices]['id'].tolist()
        return ranked_ids

# Example usage (for testing only)
if __name__ == "__main__":
    import pandas as pd
    import torch

    # Example candidate DataFrame
    df_candidates = pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['Choc A', 'Choc B', 'Choc C']
    })

    # Fake embeddings (normally from ChannelBEncoder)
    candidate_embeddings = torch.tensor([
        [0.1, 0.2, 0.3],
        [0.2, 0.1, 0.4],
        [0.05, 0.2, 0.1]
    ], dtype=torch.float32)

    # Example query embedding
    query_embedding = torch.tensor([0.1, 0.2, 0.25], dtype=torch.float32)

    scorer = ChannelBScorer()
    top_ids = scorer.rank_candidates(df_candidates, candidate_embeddings, query_embedding, top_k=2)
    print("Top ranked IDs:", top_ids)