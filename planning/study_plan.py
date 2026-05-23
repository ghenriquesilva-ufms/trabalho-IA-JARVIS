from typing import Dict, List

from llm_client import send_message
from tools.agenda import consultar_agenda
from tools.rag import buscar_material_rag
from tools.tarefas import listar_tarefas


def gerar_plano_estudos(objetivo: str) -> str:
    agenda_hoje = consultar_agenda("hoje")
    tarefas_pendentes = listar_tarefas("pendente")
    materiais = buscar_material_rag(objetivo)

    messages: List[Dict[str, str]] = [
        {
            "role": "user",
            "content": (
                "Crie um plano de estudos objetivo para o estudante, usando agenda, tarefas e materiais. "
                "Priorize o que e mais urgente e sugira blocos de estudo.\n\n"
                f"Objetivo: {objetivo}\n\nAgenda hoje:\n{agenda_hoje}\n\n"
                f"Tarefas pendentes:\n{tarefas_pendentes}\n\n"
                f"Trechos de material:\n{materiais}"
            ),
        }
    ]

    response = send_message(messages)
    return (response.content or "").strip()


def gerar_prioridades_do_dia() -> str:
    agenda_hoje = consultar_agenda("hoje")
    tarefas_pendentes = listar_tarefas("pendente")

    messages: List[Dict[str, str]] = [
        {
            "role": "user",
            "content": (
                "Com base na agenda de hoje e nas tarefas pendentes, "
                "liste as 3 prioridades do dia e justifique brevemente cada uma. "
                "Se nao houver eventos, foque nas tarefas.
\n\n"
                f"Agenda hoje:\n{agenda_hoje}\n\n"
                f"Tarefas pendentes:\n{tarefas_pendentes}"
            ),
        }
    ]

    response = send_message(messages)
    return (response.content or "").strip()
