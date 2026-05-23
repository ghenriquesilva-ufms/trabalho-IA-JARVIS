import sys
import csv
import os
from pathlib import Path
from datetime import datetime
from typing import List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_client import send_message
from tools.rag import buscar_material_rag


_TEMPLATE_PATH = os.path.join("data", "evaluation_template.csv")
_OUTPUT_PATH = os.path.join("data", "evaluation_results.csv")


def _load_questions(path: str) -> List[dict]:
    with open(path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return [row for row in reader]


def _save_results(rows: List[dict], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys(), quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)


def _clean_cell(text: str) -> str:
    normalized = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    return " | ".join(part.strip() for part in normalized.split("\n") if part.strip())


def _ask_llm(question: str, context: str) -> str:
    messages = [
        {
            "role": "user",
            "content": (
                "Responda a pergunta usando apenas os trechos fornecidos. "
                "Se faltar informacao, diga que nao encontrou no material.\n\n"
                f"Pergunta: {question}\n\nTrechos:\n{context}"
            ),
        }
    ]
    response = send_message(messages)
    return (response.content or "").strip()


def main() -> None:
    if not os.path.exists(_TEMPLATE_PATH):
        raise FileNotFoundError(f"Template nao encontrado: {_TEMPLATE_PATH}")

    rows = _load_questions(_TEMPLATE_PATH)
    for row in rows:
        question = (row.get("pergunta") or "").strip()
        if not question:
            continue
        context = buscar_material_rag(question)
        answer = _ask_llm(question, context)
        row["docs_recuperados"] = _clean_cell(context)
        row["resposta"] = _clean_cell(answer)
        row["classificacao"] = ""
        row["observacoes"] = f"Gerado em {datetime.now().isoformat(timespec='seconds')}"

    _save_results(rows, _OUTPUT_PATH)
    print(f"Resultados salvos em {_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
