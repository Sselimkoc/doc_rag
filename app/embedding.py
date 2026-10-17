import json
import os
import urllib.request

import numpy as np

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "bge-m3")
BATCH_SIZE = 32


def embed(texts: list[str]) -> np.ndarray:
    """Metinleri Ollama ile vektöre çevirir; satırlar birim uzunlukta float32."""
    vectors = []
    for i in range(0, len(texts), BATCH_SIZE):
        request = urllib.request.Request(
            f"{OLLAMA_URL}/api/embed",
            data=json.dumps({"model": EMBED_MODEL, "input": texts[i : i + BATCH_SIZE]}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=300) as response:
            vectors += json.load(response)["embeddings"]
    matrix = np.array(vectors, dtype=np.float32).reshape(len(texts), -1)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.where(norms == 0, 1, norms)
