from typing import Dict, List

import numpy as np
from sentence_transformers import SentenceTransformer


_MODEL = None


def _get_model() -> SentenceTransformer:
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _MODEL


def _cosine_similarity(matrix: np.ndarray, vector: np.ndarray) -> np.ndarray:
    vector_norm = np.linalg.norm(vector)
    matrix_norm = np.linalg.norm(matrix, axis=1)
    if vector_norm == 0:
        return np.zeros(matrix.shape[0])
    return (matrix @ vector) / (matrix_norm * vector_norm + 1e-12)


def search(query: str, index: List[Dict[str, object]], top_k: int = 3) -> List[Dict[str, object]]:
    if not index:
        return []

    model = _get_model()
    query_vec = model.encode([query], normalize_embeddings=True)[0]
    matrix = np.array([item.get("embedding", []) for item in index], dtype=float)
    scores = _cosine_similarity(matrix, query_vec)

    ranked_indices = np.argsort(scores)[::-1][:top_k]
    results = []
    for idx in ranked_indices:
        item = dict(index[idx])
        item["score"] = float(scores[idx])
        results.append(item)

    return results
