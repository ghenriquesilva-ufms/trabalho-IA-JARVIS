import csv
import os


_TEMPLATE_PATH = os.path.join("data", "evaluation_template.csv")

QUESTIONS = [
    "Explique regressao logistica.",
    "Resuma o conteudo sobre embeddings.",
    "Quais sao os principais pontos do material X?",
    "Qual a diferenca entre classificacao e regressao?",
    "O que e overfitting e como evitar?",
    "Descreva validacao cruzada.",
    "O que e regularizacao L2?",
    "Para que serve a funcao sigmoide?",
    "Explique matriz de confusao.",
    "O que e recall e precision?",
]


def main() -> None:
    if not os.path.exists(_TEMPLATE_PATH):
        raise FileNotFoundError(f"Template nao encontrado: {_TEMPLATE_PATH}")

    rows = []
    for idx, question in enumerate(QUESTIONS, start=1):
        rows.append(
            {
                "id": idx,
                "pergunta": question,
                "docs_recuperados": "",
                "resposta": "",
                "classificacao": "",
                "observacoes": "",
            }
        )

    with open(_TEMPLATE_PATH, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "id",
                "pergunta",
                "docs_recuperados",
                "resposta",
                "classificacao",
                "observacoes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Template preenchido em {_TEMPLATE_PATH}")


if __name__ == "__main__":
    main()
