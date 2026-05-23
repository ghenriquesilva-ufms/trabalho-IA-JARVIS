from typing import List

from rag.embedder import load_index
from rag.retriever import search


_INDEX = load_index()


def _format_result(item: dict, position: int) -> str:
    source = item.get("source", "")
    text = item.get("text", "")
    score = item.get("score", 0.0)
    return f"[{position}] {source} (score={score:.3f})\n{text}"


def buscar_material_rag(pergunta: str) -> str:
    global _INDEX
    if not _INDEX:
        _INDEX = load_index()
    if not _INDEX:
        return "Indice vazio. Gere embeddings antes de buscar."

    results: List[dict] = search(pergunta, _INDEX)
    if not results:
        return "Nenhum trecho encontrado."

    return "\n\n".join(_format_result(item, i + 1) for i, item in enumerate(results))
