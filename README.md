# RAG Docs Assistant

A question-answering assistant over the official **FastAPI documentation**. It answers with grounded code, cites the pages it used, and says "I don't know" when the docs don't cover the question.

**Live demo:** https://rag-docs-assistant-e96h.onrender.com
**Stack:** Python · FastAPI · ChromaDB · Claude API (Haiku for answers, Sonnet as judge) · Docker · Render

The interesting part is not the chatbot. It's the **evaluation harness** and the **10 measured versions** it drove: answer correctness went from **26% to 87%** (v9, live), and every change was kept or rejected based on numbers.

---

## How it works

**Ingestion**

- 155 FastAPI doc pages → ~2,400 chunks in ChromaDB.
- Code samples that the docs pull in from separate files are **inlined** (the first version was indexing the include tag instead of the code).
- **Heading-aware chunking** that never splits a code block; each chunk is labelled `Page > Section`.
- Changelog and auto-generated API-reference pages are excluded from retrieval with metadata filters.

**Retrieval (v9, live)**

- Vector search, top 5 chunks.
- **Neighbour expansion:** each retrieved chunk is sent together with the chunk before and after it on the same page, joined in reading order. Questions are written in prose, so they match prose chunks; the code usually sits in the next chunk.

**Generation**

- Claude Haiku, `temperature=0`, with a grounding rule: only use code that appears in the context, never invent parameters or values.
- Refuses with "I don't know" when the context doesn't answer the question.

**Serving**

- FastAPI app, Docker, deployed on Render, per-IP rate limiting.

**Agent (v10, experiment, `agent.py`)**

- Claude gets two tools, `search_docs(query)` and `read_page(source)`, and decides what to search and how many times.
- Hand-written tool loop on the Claude API (no framework): capped at 5 rounds, tool errors returned to the model as text instead of crashing, first round forced to be a tool call (`tool_choice: any`).
- Returns the answer, sources, a trace of every tool call, and the exact text the tools returned (used by the faithfulness judge).

---

## How it's evaluated

- **30 test questions:** direct, paraphrased, multi-page, out-of-scope, and near-miss questions it must refuse (Django, Celery, AWS Lambda…).
- **Retrieval hit@5:** did the right source page come back? Checked against pages listed by hand. Free, no API calls.
- **Correctness:** a separate, stronger model (Sonnet) checks the answer against **key facts written by hand** for each question.
- **Faithfulness:** the judge gets only the answer and the text the bot actually read, and lists every claim that isn't supported by it. For the agent, that text is the recorded tool output, not a re-run of the search.
- **Behaviour:** answers when it should, refuses when it should.
- Verdicts are cached on their exact inputs and saved after every question, so a re-run only pays for what changed.

---

## Results

Correct and faithful are out of 23 answerable questions.

| Version       | Change                                                         | Retrieval | Correct | Faithful |
| ------------- | -------------------------------------------------------------- | --------- | ------- | -------- |
| v1            | Baseline                                                       | 74%       | 26%     | 35%      |
| v2            | Inlined code samples the docs load from separate files         |           | 39%     | 52%      |
| v3–v5         | Heading-aware chunking; filtered changelog and reference pages |           | 43%     | 70%      |
| v6            | Retrieve top 5 instead of top 3                                |           | 70%     | 57%      |
| v7            | Grounding rule: only use code that appears in the context      | 96%       | 61%     | 65%      |
| v8            | Hybrid BM25 + vector search (**not shipped**)                  |           | 48%     | 74%      |
| —             | Cross-encoder reranker, 4 models (**not shipped**)             | 83%       | —       | —        |
| **v9 (live)** | **Neighbour-chunk expansion**                                  | **96%**   | **87%** | **83%**  |
| v10           | Tool-calling agent (experiment)                                | **100%**  | 91%     | 74%      |

---

## Decisions worth explaining

- **The first number was wrong.** An early test claimed 94%. A proper eval showed 26%: ingestion was saving placeholder lines instead of code.
- **Correctness vs faithfulness is a real trade-off.** Top-5 retrieval made answers more complete but the model started inventing parameters. A grounding rule recovered most of it.
- **Hybrid search and reranking were built, measured and rejected.** Retrieval already found the right page 22/23 times; keyword matching and web-trained rerankers pushed paraphrased questions down.
- **The real bottleneck was what the model received, not search.** Reading the failures showed answers with the right idea but no code: the code was in the next chunk. Neighbour expansion took correctness from 61% to 87% and faithfulness from 65% to 83%, the first change where both went up.
- **The agent finds more but invents more.** It reached 100% retrieval and fixed multi-part questions, but faithfulness dropped (83% → 74%): it stitched code from two pages together, and filled gaps when a page was cut off by the read limit. It's also ~1.4× the cost and ~2× the latency. v9 stays live.
- **Some rules belong in code, not in the prompt.** Three prompt versions couldn't stop the agent from refusing without searching. Forcing the first round to be a tool call fixed it in one line.

---

## Known limitations

- Comparison questions (e.g. FastAPI vs Flask) still fail: the docs don't compare directly, and the bot hedges.
- The agent's `read_page` truncates long pages, which caused at least one invented answer.
- 23 answerable questions is small: one question is ~4%, so differences of ±2 are noise.

## Next

- A verification step that checks every code line in the answer against the tool results.
- Stronger generator (Sonnet) as an experiment, to find the quality ceiling and its cost.
- A larger eval set (50–100 questions).

---

## Run the evaluation

```bash
pip install -r requirements.txt
# needs ANTHROPIC_API_KEY in .env

python -c "from eval_runner import run_eval; run_eval('v9')"                  # v9 pipeline
python -c "from eval_runner import run_eval; run_eval('v10', mode='agent')"   # agent
python judge.py          # set RESULTS_FILE / JUDGED_FILE at the top first
python retrieval_check.py  # free retrieval check
python agent.py          # try the agent on two sample questions
```
