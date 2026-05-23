import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rag.chunker import chunk_documents
from rag.embedder import generate_embeddings, save_index
from rag.loader import load_documents
from tools.agenda import consultar_agenda
from tools import rag as rag_module
from tools.rag import buscar_material_rag
from tools.tarefas import adicionar_tarefa, listar_tarefas


DOCS_PATH = ROOT / "data" / "docs"


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def test_docs_load() -> None:
    docs = load_documents(str(DOCS_PATH))
    _check(len(docs) >= 10, "Esperado pelo menos 10 documentos em data/docs.")


def test_chunk_and_embed() -> None:
    docs = load_documents(str(DOCS_PATH))
    chunks = chunk_documents(docs)
    _check(len(chunks) > 0, "Chunking retornou vazio.")
    embeddings = generate_embeddings(chunks[:5])
    _check("embedding" in embeddings[0], "Embedding nao foi gerado.")


def test_rag_search() -> None:
    docs = load_documents(str(DOCS_PATH))
    chunks = chunk_documents(docs)
    embeddings = generate_embeddings(chunks)
    index_path = ROOT / "data" / "index.pkl"
    save_index(embeddings, str(index_path))
    rag_module._INDEX = rag_module.load_index(str(index_path))
    result = buscar_material_rag("regressao logistica")
    _check("Indice vazio" not in result, "Indice RAG vazio.")


def test_tasks_flow() -> None:
    adicionar_tarefa("Teste de tarefa", "2026-12-01", "Teste")
    tasks_text = listar_tarefas("pendente")
    _check("Teste de tarefa" in tasks_text, "Tarefa nao aparece na listagem.")


def test_agenda_flow() -> None:
    response = consultar_agenda("hoje")
    _check(isinstance(response, str), "Resposta da agenda deve ser string.")


def main() -> None:
    print("[1/5] docs load")
    test_docs_load()
    print("[2/5] chunk + embed")
    test_chunk_and_embed()
    print("[3/5] rag search")
    test_rag_search()
    print("[4/5] tasks flow")
    test_tasks_flow()
    print("[5/5] agenda flow")
    test_agenda_flow()
    print("OK: testes basicos concluídos.")


if __name__ == "__main__":
    main()
