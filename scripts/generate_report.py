import csv
import os
from datetime import datetime


EVAL_PATH = os.path.join("data", "evaluation_results.csv")
ERROR_PATH = os.path.join("data", "error_analysis_template.csv")
OUTPUT_PATH = os.path.join("data", "report.md")


def _read_csv(path: str):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _count_by_classification(rows):
    counts = {"correta": 0, "parcialmente correta": 0, "incorreta": 0, "": 0}
    for row in rows:
        key = (row.get("classificacao") or "").strip().lower()
        counts[key] = counts.get(key, 0) + 1
    return counts


def main() -> None:
    eval_rows = _read_csv(EVAL_PATH)
    error_rows = _read_csv(ERROR_PATH)

    counts = _count_by_classification(eval_rows)
    timestamp = datetime.now().isoformat(timespec="seconds")

    lines = []
    lines.append("# Relatorio de avaliacao\n")
    lines.append(f"Gerado em: {timestamp}\n")

    lines.append("## Resumo das classificacoes\n")
    lines.append(f"- correta: {counts.get('correta', 0)}")
    lines.append(f"- parcialmente correta: {counts.get('parcialmente correta', 0)}")
    lines.append(f"- incorreta: {counts.get('incorreta', 0)}")
    lines.append("")

    lines.append("## Avaliacao (10 perguntas)\n")
    for row in eval_rows:
        q = row.get("pergunta", "")
        c = row.get("classificacao", "")
        obs = row.get("observacoes", "")
        lines.append(f"- Pergunta: {q}")
        lines.append(f"  - Classificacao: {c}")
        if obs:
            lines.append(f"  - Observacoes: {obs}")
    lines.append("")

    lines.append("## Analise de erros (3 falhas)\n")
    for row in error_rows:
        q = row.get("pergunta", "")
        t = row.get("tipo_falha", "")
        causa = row.get("causa", "")
        sol = row.get("possivel_solucao", "")
        if not q:
            continue
        lines.append(f"- Pergunta: {q}")
        lines.append(f"  - Tipo: {t}")
        lines.append(f"  - Causa: {causa}")
        lines.append(f"  - Possivel solucao: {sol}")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    print(f"Relatorio salvo em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
