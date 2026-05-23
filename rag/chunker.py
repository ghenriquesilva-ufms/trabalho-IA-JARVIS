from typing import Dict, List


def chunk_documents(
    docs: List[Dict[str, str]],
    chunk_size: int = 500,
    overlap: int = 50,
) -> List[Dict[str, str]]:
    chunks: List[Dict[str, str]] = []
    step = max(chunk_size - overlap, 1)

    for doc in docs:
        text = doc.get("content", "")
        source = doc.get("source", doc.get("filename", ""))
        if not text:
            continue

        for start in range(0, len(text), step):
            end = start + chunk_size
            chunk_text = text[start:end].strip()
            if not chunk_text:
                continue
            chunk_id = f"{source}:{start}-{end}"
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "source": source,
                    "text": chunk_text,
                }
            )

    return chunks
