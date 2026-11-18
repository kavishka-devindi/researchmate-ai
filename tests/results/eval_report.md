# Evaluation report

- Date: 2026-11-19 03:13
- Chat model: `gemini-3.5-flash-lite`, agent model: `gemini-3.5-flash-lite`, embedding model: `gemini-embedding-001`
- Retrieval: top 6 passages, minimum similarity 0.6, chunk size 800, overlap 150
- Questions run: 22 (17 answerable, 5 unanswerable)
- Agent evaluated: yes

| Measure | Result |
|---|---|
| Retrieval hit rate @6 (expected page in top results) | 14/15 (93.3%) |
| Retrieval mean reciprocal rank | 0.75 |
| Direct RAG: answered when answerable | 15/15 (100.0%) |
| Direct RAG: refused when unanswerable | 5/5 (100.0%) |
| Direct RAG: citations pointing to a real page | 38/39 (97.4%) |
| Direct RAG: citations found in the retrieved passages | 38/39 (97.4%) |
| Direct RAG: expected page cited | 13/15 (86.7%) |
| Direct RAG: median / slowest response time | 1.9 s / 3.8 s |
| Agent: answered when answerable | 17/17 (100.0%) |
| Agent: refused when unanswerable | 5/5 (100.0%) |
| Agent: citations pointing to a real page | 53/53 (100.0%) |
| Agent: expected page cited | 12/15 (80.0%) |
| Agent: median / slowest response time | 4.6 s / 29.7 s |
| Agent: acceptable tool chosen | 22/22 (100.0%) |

Answer faithfulness is judged by hand. See `faithfulness_sheet.csv`.

## Failures

| Question id | Where | What went wrong | Question |
|---|---|---|---|
| 9 | rag | expected page not cited | What is the Transformer architecture based on? |
| 9 | rag | cited a page that does not exist | What is the Transformer architecture based on? |
| 9 | rag | cited a page that was not retrieved | What is the Transformer architecture based on? |
| 15 | agent | expected page not cited | Why is a layer between source systems and the warehouse useful? |
| 18 | agent | expected page not cited | What is the value of d_model in the base Transformer architecture? |
| 22 | rag | expected page not cited | What is self-attention? |
| 22 | agent | expected page not cited | What is self-attention? |
| 22 | retrieval | expected page not in top results | What is self-attention? |
