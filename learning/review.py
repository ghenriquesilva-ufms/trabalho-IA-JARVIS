from typing import Dict, List

from llm_client import send_message


def recomendar_revisao(topic: str, context: str) -> str:
    messages: List[Dict[str, str]] = [
        {
            "role": "user",
            "content": (
                "Gere um plano curto de revisao com foco nos pontos-chave e em lacunas comuns. "
                "Use apenas o contexto fornecido e sugira 3 a 5 acoes.\n\n"
                f"Topico: {topic}\n\nContexto:\n{context}"
            ),
        }
    ]
    response = send_message(messages)
    return (response.content or "").strip()
