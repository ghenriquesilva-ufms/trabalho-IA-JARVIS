import os
import pickle
from typing import Dict, List

from sentence_transformers import SentenceTransformer


_MODEL = None


def _get_model() -> SentenceTransformer:
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _MODEL


def generate_embeddings(chunks: List[Dict[str, str]]) -> List[Dict[str, object]]:
    model = _get_model()
    texts = [chunk.get("text", "") for chunk in chunks]
    embeddings = model.encode(texts, normalize_embeddings=True).tolist()

    enriched: List[Dict[str, object]] = []
    for chunk, embedding in zip(chunks, embeddings):
        new_chunk = dict(chunk)
        new_chunk["embedding"] = embedding
        enriched.append(new_chunk)

    return enriched


def save_index(chunks_com_embeddings: List[Dict[str, object]], path: str = "data/index.pkl") -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as file:
        pickle.dump(chunks_com_embeddings, file)


def load_index(path: str = "data/index.pkl") -> List[Dict[str, object]]:
    try:
        with open(path, "rb") as file:
            return pickle.load(file)
    except FileNotFoundError:
        return []
