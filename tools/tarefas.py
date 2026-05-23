import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "tarefas.json")


def _load_tasks() -> List[Dict[str, Any]]:
    if not os.path.exists(_DATA_PATH):
        return []
    with open(_DATA_PATH, "r", encoding="utf-8") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return []


def _save_tasks(tasks: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(_DATA_PATH), exist_ok=True)
    with open(_DATA_PATH, "w", encoding="utf-8") as file:
        json.dump(tasks, file, ensure_ascii=False, indent=2)


def _next_id(tasks: List[Dict[str, Any]]) -> int:
    if not tasks:
        return 1
    return max(task.get("id", 0) for task in tasks) + 1


def listar_tarefas(status: str = "pendente") -> str:
    tasks = _load_tasks()
    if not tasks:
        return "Nenhuma tarefa encontrada."

    normalized_status = status.lower()
    filtered = [task for task in tasks if task.get("status") == normalized_status]
    if not filtered:
        return "Nenhuma tarefa encontrada."

    filtered.sort(key=lambda task: (task.get("prazo") or "", task.get("id", 0)))
    lines = []
    for task in filtered:
        task_id = task.get("id")
        titulo = task.get("titulo", "(sem titulo)")
        prazo = task.get("prazo") or "sem prazo"
        materia = task.get("materia") or "sem materia"
        lines.append(f"#{task_id} | {titulo} | {materia} | prazo: {prazo}")
    return "\n".join(lines)


def adicionar_tarefa(titulo: str, prazo: str = None, materia: str = None) -> str:
    tasks = _load_tasks()
    task_id = _next_id(tasks)
    tasks.append(
        {
            "id": task_id,
            "titulo": titulo,
            "prazo": prazo,
            "materia": materia,
            "status": "pendente",
            "criada_em": datetime.now().isoformat(timespec="seconds"),
        }
    )
    _save_tasks(tasks)
    return f"Tarefa criada: #{task_id} - {titulo}"


def concluir_tarefa(id: int) -> str:
    tasks = _load_tasks()
    for task in tasks:
        if task.get("id") == id:
            task["status"] = "concluida"
            _save_tasks(tasks)
            return f"Tarefa concluida: #{id} - {task.get('titulo', '')}"
    return f"Tarefa nao encontrada: #{id}"
