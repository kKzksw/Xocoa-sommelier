import json
from pathlib import Path
from channel_b.embeddings.encoder import EmbeddingEncoder
from channel_b.embeddings.schema import build_embedding_text

DATA_PATH = Path("Xoc/data/chocolates.json")
OUTPUT_PATH = Path("Xoc/data/chocolate_embeddings.json")


def build_embeddings():
    encoder = EmbeddingEncoder()

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        products = json.load(f)

    output = []

    for product in products:
        text = build_embedding_text(product)
        if not text.strip():
            continue

        output.append({
            "id": product["id"],
            "embedding": encoder.encode(text),
            "text_hash": encoder.hash_text(text),
        })

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Saved {len(output)} embeddings to {OUTPUT_PATH}")


if __name__ == "__main__":
    build_embeddings()
