from sentence_transformers import SentenceTransformer
import hashlib

MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"


class EmbeddingEncoder:
    def __init__(self, model_name: str = MODEL_NAME):
        self.model = SentenceTransformer(model_name)

    def encode(self, text: str) -> list[float]:
        return self.model.encode(text, normalize_embeddings=True).tolist()

    @staticmethod
    def hash_text(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
