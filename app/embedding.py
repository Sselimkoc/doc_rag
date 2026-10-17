import numpy as np

from app.config import EMBED_MODEL
from app.ollama import post

BATCH_SIZE = 32


def embed(texts: list[str]) -> np.ndarray:
    """Metinleri Ollama ile vektöre çevirir; satırlar birim uzunlukta float32."""
    vectors = []
    for i in range(0, len(texts), BATCH_SIZE):
        vectors += post("/api/embed", {"model": EMBED_MODEL, "input": texts[i : i + BATCH_SIZE]})["embeddings"]
    matrix = np.array(vectors, dtype=np.float32).reshape(len(texts), -1)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.where(norms == 0, 1, norms)
