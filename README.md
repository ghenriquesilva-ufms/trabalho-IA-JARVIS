<<<<<<< HEAD
# trabalho-IA-JARVIS
Trabalho de Inteligência Artificial na Universidade Federal de Mato Grosso do Sul, onde foi criado um assistente inteligente para fins de uso estudantil.
=======
# JARVIS Academico

Assistente academico com RAG, agenda, tarefas, planejamento de estudos e modulos de aprendizado.

## Requisitos
- Python 3.10+
- Dependencias:
  - openai
  - sentence-transformers
  - pdfplumber ou PyPDF2
  - numpy

Instalacao:

```bash
py -m pip install openai sentence-transformers pdfplumber PyPDF2 numpy
```

## Executar (CLI)

O trabalho tambem pode ser executado pelo terminal ao invés de uma interface.

1) Gere o indice RAG:

```bash
py -c "from rag.loader import load_documents; from rag.chunker import chunk_documents; from rag.embedder import generate_embeddings, save_index; docs=load_documents('data/docs'); chunks=chunk_documents(docs); embeddings=generate_embeddings(chunks); save_index(embeddings, 'data/index.pkl'); print(f'Docs: {len(docs)} | Chunks: {len(chunks)} | Index salvo.')"
```

2) Rode o assistente:

```bash
py main.py
```

Comandos:
- !hoje
- !tarefas
- !quiz <materia>
- !revisao <materia>
- !plano <objetivo>
- !prioridades

## Executar (UI)

```bash
py ui/app.py
```

A UI inclui:
- chat com a LLM
- botao para gerar embeddings
- botao para buscar RAG
- quiz interativo
- revisao
- tarefas com edicao e conclusao

## Dataset

A pasta data/docs contem 10 documentos curtos, com resumos livres de temas academicos:
- regressao_logistica.txt
- embeddings.txt
- classificacao_vs_regressao.txt
- overfitting.txt
- validacao_cruzada.txt
- regularizacao_l2.txt
- funcao_sigmoide.txt
- matriz_confusao.txt
- precision_recall.txt
- embeddings_semantica.txt

Documentacao completa do dataset: data/dataset_info.md

### Estrategia de chunking
Detalhada em data/dataset_info.md.

## Avaliacao

1) Preencha perguntas em data/evaluation_template.csv
2) Rode:

```bash
py scripts/run_evaluation.py
```

3) Classifique as respostas em data/evaluation_results.csv

## Analise de erros

Preencha data/error_analysis_template.csv com 3 falhas:
- tipo (recuperacao, geracao, ambiguidade)
- causa
- possivel solucao

## Tool calling

O sistema implementa 5 ferramentas e loga chamadas em data/logs.json. O servidor Gemma fornecido nao esta habilitado para tool calling (erro 400). O cliente e o fluxo estao prontos, mas dependem da configuracao do servidor.

## IAs utilizadas

- GitHub Copilot
- Claude

## Estrutura do projeto

- main.py
- llm_client.py
- rag/
- tools/
- learning/
- planning/
- ui/
- data/
- scripts/

## Observacoes

- Para remover warnings do HF Hub, configure HF_TOKEN (opcional).
>>>>>>> 8f13094 (Initial commit)
