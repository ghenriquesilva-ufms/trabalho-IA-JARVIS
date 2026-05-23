import json
from typing import Any, Dict, List

from llm_client import send_message


def _build_quiz_prompt(topic: str, context: str) -> List[Dict[str, str]]:
    return [
        {
            "role": "user",
            "content": (
                "Gere 3 perguntas de multipla escolha sobre o topico indicado. "
                "Use apenas o contexto fornecido. Retorne JSON puro sem markdown. "
                "Formato: lista de objetos com chaves: pergunta (string), "
                "opcoes (lista de 4 strings), resposta_correta (inteiro 1-4).\n\n"
                f"Topico: {topic}\n\nContexto:\n{context}"
            ),
        }
    ]


def generate_quiz(topic: str, context: str) -> List[Dict[str, Any]]:
    messages = _build_quiz_prompt(topic, context)
    try:
        response = send_message(messages)
    except Exception:
        return []
    content = (response.content or "").strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        extracted = _extract_json_array(content)
        if extracted:
            return extracted
        return []


def _extract_json_array(text: str) -> List[Dict[str, Any]] | None:
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def _build_feedback_prompt(topic: str, acertos: int, total: int) -> List[Dict[str, str]]:
    return [
        {
            "role": "user",
            "content": (
                "Gere um feedback curto e motivador para o estudante com base no desempenho. "
                "Mencione o topico e sugira proximos passos de estudo.\n\n"
                f"Topico: {topic}\nAcertos: {acertos}\nTotal: {total}"
            ),
        }
    ]


def run_quiz_session(topic: str, context: str) -> Dict[str, Any]:
    quiz = generate_quiz(topic, context)
    if not quiz:
        print("Nao foi possivel gerar o quiz. Tente novamente.")
        return {"acertos": 0, "total": 0, "feedback": "Quiz nao gerado."}
    total = len(quiz)
    acertos = 0

    for idx, item in enumerate(quiz, start=1):
        pergunta = item.get("pergunta", "")
        opcoes = item.get("opcoes", [])
        correta = item.get("resposta_correta", 0)

        print(f"\nPergunta {idx}: {pergunta}")
        for opt_idx, option in enumerate(opcoes, start=1):
            print(f"  {opt_idx}. {option}")

        escolha = None
        while escolha is None:
            entrada = input("Resposta (1-4): ").strip()
            if entrada.isdigit() and 1 <= int(entrada) <= 4:
                escolha = int(entrada)
            else:
                print("Entrada invalida. Digite um numero de 1 a 4.")

        if escolha == correta:
            print("Correto!")
            acertos += 1
        else:
            print(f"Incorreto. Resposta correta: {correta}.")

    feedback_response = send_message(_build_feedback_prompt(topic, acertos, total))
    feedback = (feedback_response.content or "").strip()

    print(f"\nPontuacao: {acertos}/{total}")
    print(f"Feedback: {feedback}")

    return {"acertos": acertos, "total": total, "feedback": feedback}
