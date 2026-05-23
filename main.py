import json
import os
from datetime import datetime
from typing import Any, Dict, List

from llm_client import send_message
from learning.active_recall import run_quiz_session
from learning.review import recomendar_revisao
from planning.study_plan import gerar_plano_estudos, gerar_prioridades_do_dia
from tools.agenda import consultar_agenda
from tools.rag import buscar_material_rag
from tools.tarefas import adicionar_tarefa, concluir_tarefa, listar_tarefas


TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "consultar_agenda",
            "description": "Consulta eventos na agenda por data, hoje, amanha ou dia da semana.",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "Data em YYYY-MM-DD, ou palavras como hoje, amanha, segunda.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "listar_tarefas",
            "description": "Lista tarefas por status (pendente ou concluida).",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Status da tarefa: pendente ou concluida.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "adicionar_tarefa",
            "description": "Adiciona uma nova tarefa com titulo, prazo e materia.",
            "parameters": {
                "type": "object",
                "properties": {
                    "titulo": {"type": "string", "description": "Titulo da tarefa."},
                    "prazo": {
                        "type": "string",
                        "description": "Prazo em YYYY-MM-DD (opcional).",
                    },
                    "materia": {"type": "string", "description": "Materia (opcional)."},
                },
                "required": ["titulo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "concluir_tarefa",
            "description": "Marca uma tarefa como concluida pelo id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "description": "ID da tarefa."},
                },
                "required": ["id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_material_rag",
            "description": "Busca trechos relevantes em documentos locais via RAG.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pergunta": {
                        "type": "string",
                        "description": "Pergunta para busca no material.",
                    }
                },
                "required": ["pergunta"],
            },
        },
    },
]

TOOL_FUNCTIONS = {
    "consultar_agenda": consultar_agenda,
    "listar_tarefas": listar_tarefas,
    "adicionar_tarefa": adicionar_tarefa,
    "concluir_tarefa": concluir_tarefa,
    "buscar_material_rag": buscar_material_rag,
}

_LOG_PATH = os.path.join(os.path.dirname(__file__), "data", "logs.json")


def log_tool_call(tool_name: str, input_args: Dict[str, Any], output: Any) -> None:
    os.makedirs(os.path.dirname(_LOG_PATH), exist_ok=True)
    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "tool_name": tool_name,
        "input": input_args,
        "output": output,
    }

    logs = []
    if os.path.exists(_LOG_PATH):
        try:
            with open(_LOG_PATH, "r", encoding="utf-8") as file:
                logs = json.load(file)
        except json.JSONDecodeError:
            logs = []

    logs.append(entry)
    with open(_LOG_PATH, "w", encoding="utf-8") as file:
        json.dump(logs, file, ensure_ascii=False, indent=2)


def _tool_schema_text() -> str:
    items = []
    for tool in TOOLS_SCHEMA:
        fn = tool.get("function", {})
        items.append(
            {
                "name": fn.get("name"),
                "description": fn.get("description"),
                "parameters": fn.get("parameters"),
            }
        )
    return json.dumps(items, ensure_ascii=False)


def _extract_json_object(text: str) -> Dict[str, Any] | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def _decide_tool(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    system_prompt = (
        "Voce deve decidir se usa uma ferramenta. "
        "Responda SOMENTE em JSON com o formato: "
        '"{\\"tool\\": \\"nome_da_ferramenta\\" ou \\"none\\", \\"args\\": {..}, \\"response\\": \\"texto\\"}". '
        "Se tool != none, response deve ser vazio. "
        "Se tool == none, response deve conter a resposta final. "
        "Ferramentas disponiveis (JSON): "
        + _tool_schema_text()
    )
    tool_messages = [{"role": "system", "content": system_prompt}] + messages
    response = send_message(tool_messages)
    content = (response.content or "").strip()
    parsed = _extract_json_object(content)
    if parsed is None:
        return {"tool": "none", "args": {}, "response": content}
    return parsed


def run_conversation(user_input: str, history: List[Dict[str, Any]]) -> str:
    history.append({"role": "user", "content": user_input})
    decision = _decide_tool(history)
    tool_name = decision.get("tool", "none")
    input_args = decision.get("args") or {}
    if tool_name == "none":
        response_text = decision.get("response") or ""
        history.append({"role": "assistant", "content": response_text})
        return response_text

    tool_fn = TOOL_FUNCTIONS.get(tool_name)
    if tool_fn is None:
        tool_output = f"Tool desconhecida: {tool_name}"
    else:
        try:
            tool_output = tool_fn(**input_args)
        except Exception as exc:
            tool_output = f"Erro ao executar {tool_name}: {exc}"

    log_tool_call(tool_name, input_args, tool_output)
    history.append({"role": "assistant", "content": "Ferramenta executada."})
    history.append(
        {
            "role": "user",
            "content": (
                "Resultado da ferramenta:\n" + tool_output + "\n\nResponda ao usuario."
            ),
        }
    )

    final_response = send_message(history)
    response_text = final_response.content or ""
    history.append({"role": "assistant", "content": response_text})
    return response_text


def main() -> None:
    history: List[Dict[str, Any]] = []
    while True:
        user_input = input("> ").strip()
        if user_input.lower() == "sair":
            break
        if not user_input:
            continue
        if user_input.startswith("!quiz"):
            topic = user_input[len("!quiz") :].strip()
            if not topic:
                print("Use: !quiz <materia>")
                continue
            context = buscar_material_rag(topic)
            run_quiz_session(topic, context)
            continue
        if user_input.startswith("!revisao"):
            topic = user_input[len("!revisao") :].strip()
            if not topic:
                print("Use: !revisao <materia>")
                continue
            context = buscar_material_rag(topic)
            print(recomendar_revisao(topic, context))
            continue
        if user_input.startswith("!plano"):
            objetivo = user_input[len("!plano") :].strip()
            if not objetivo:
                print("Use: !plano <objetivo>")
                continue
            print(gerar_plano_estudos(objetivo))
            continue
        if user_input == "!prioridades":
            print(gerar_prioridades_do_dia())
            continue
        if user_input == "!tarefas":
            print(listar_tarefas("pendente"))
            continue
        if user_input == "!hoje":
            print(consultar_agenda("hoje"))
            continue
        response = run_conversation(user_input, history)
        print(response)


if __name__ == "__main__":
    main()
