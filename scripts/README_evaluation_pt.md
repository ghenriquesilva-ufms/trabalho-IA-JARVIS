# Avaliacao do sistema (passo a passo)

1) Preencha 10 perguntas em data/evaluation_template.csv.

Opcional (preenche exemplo):
```bash
py scripts/fill_evaluation_template.py
```

2) Gere respostas e trechos recuperados:
```bash
py scripts/run_evaluation.py
```

3) Abra data/evaluation_results.csv e preencha a coluna classificacao:
- correta
- parcialmente correta
- incorreta

4) Use observacoes para anotar falhas (recuperacao, geracao, ambiguidade).
