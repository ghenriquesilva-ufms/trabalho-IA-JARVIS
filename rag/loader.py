import os
from typing import Dict, List


def _read_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def _read_pdf(path: str) -> str:
    try:
        import pdfplumber  # type: ignore

        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception:
        try:
            from PyPDF2 import PdfReader  # type: ignore

            reader = PdfReader(path)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            return ""


def load_documents(pasta: str = "data/docs") -> List[Dict[str, str]]:
    documents: List[Dict[str, str]] = []
    if not os.path.isdir(pasta):
        return documents

    for root, _, files in os.walk(pasta):
        for filename in files:
            lower = filename.lower()
            path = os.path.join(root, filename)
            content = ""
            if lower.endswith(".txt"):
                content = _read_txt(path)
            elif lower.endswith(".pdf"):
                content = _read_pdf(path)

            if content.strip():
                source = os.path.relpath(path, pasta)
                documents.append(
                    {
                        "filename": filename,
                        "content": content,
                        "source": source,
                    }
                )

    return documents
