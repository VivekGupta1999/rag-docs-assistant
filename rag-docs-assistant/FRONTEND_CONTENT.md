# Frontend content: RAG Docs Assistant

Exact copy for every section of `static/index.html`, top to bottom. Keep the existing layout and style; only the content changes unless a section says otherwise.

---

## 0. Page basics

- `<title>`: RAG Docs Assistant · Vivek Gupta
- Meta description: A question-answering assistant over the FastAPI docs, improved from 26% to 87% correct answers across 10 measured versions.

---

## 1. Header / hero (top of the main column)

**Title:** RAG Docs Assistant

**Tagline:** Ask anything about FastAPI. Get an answer grounded in the official docs, with sources, or an honest "I don't know".

**Stat row (4 small boxes):**
| Number | Label |
|---|---|
| 87% | correct answers (from 26%) |
| 83% | faithful to the docs (from 35%) |
| 10 | measured versions |
| 7/7 | off-topic questions refused |

**Buttons:**
- **Try it**: opens the chat widget.
- **GitHub**: https://github.com/VivekGupta1999/rag-docs-assistant
- **Read the write-up**: https://github.com/VivekGupta1999/rag-docs-assistant#readme

---

## 2. Why I built this

Most RAG demos show a chatbot and stop there. I wanted to know whether mine actually gave correct answers, and to improve it the way you'd improve any production system: measure, find the real problem, change one thing, measure again.

The first test said 94%. It was a weak test. A proper evaluation said 26%. Everything on this page is the story of getting from that real 26% to 87%, including the ideas that didn't work.

---

## 3. How it works

**Diagram:** the inline SVG from `arch.svg` (replaces the old base64 PNG).

**Paragraph:**
Ingestion runs once. FastAPI's 155 doc pages are cleaned (code samples the docs load from separate files are inlined), split by headings into about 2,400 chunks that never break a code block, embedded locally and stored in ChromaDB. Changelog and auto-generated API reference pages are filtered out.

For every question, the 5 most relevant chunks are retrieved, and each one is sent together with its neighbouring chunks from the same page, because the code usually sits right after the explanation that matches the question. Claude Haiku answers using only that context, cites its sources, and says "I don't know" when the docs don't cover the question.

---

## 4. Evaluation

**Headline table (existing `eval-table` style):**
| | |
|---|---|
| Correct answers | 20/23 (87%) |
| Faithful to the docs | 19/23 (83%) |
| Right page retrieved | 22/23 (96%) |
| Out-of-scope questions refused | 7/7 |

**Paragraph:**
30 hand-written test questions: direct, paraphrased, multi-page, and 7 the bot must refuse (Django, Celery, AWS Lambda, cooking…). A separate, stronger model (Claude Sonnet) grades every answer twice: against key facts written by hand (correctness), and against the exact text the bot was given (faithfulness, meaning whether it made anything up).

**Small note:**
An earlier version of this page showed 94%. That came from a weak test; a proper evaluation showed the real starting point was 26%.

---

## 5. The journey: 26% → 87% (NEW section)

**Image:** `static/journey.png`, full width, rounded corners, click to open full size.
Alt text: "Infographic of 10 versions: correctness rose from 26% to 87% and faithfulness from 35% to 83%. Hybrid search, a reranker and an agent were built and not shipped."

**Paragraph:**
Every change was measured on the same 30 questions and kept or thrown away based on the numbers. Hybrid search, a cross-encoder reranker and a tool-calling agent were all built and tested. The simpler pipeline stayed live.

**Version table (collapsible "See every version" under the image):**
| Version | Change | Correct | Faithful | Status |
|---|---|---|---|---|
| v1 | Baseline + honest evaluation | 26% | 35% | Shipped |
| v2 | Inlined code the docs load from separate files | 39% | 52% | Shipped |
| v3–5 | Heading-aware chunking; filtered changelog and reference pages | 43% | 70% | Shipped |
| v6 | Retrieve top 5 instead of top 3 | 70% | 57% | Shipped |
| v7 | Grounding rule: only use code that's in the context | 61% | 65% | Shipped |
| v8 | Hybrid BM25 + vector search | 48% | 74% | Not shipped |
| — | Cross-encoder reranker, 4 models (retrieval 96% → 83%) | — | — | Not shipped |
| **v9** | **Neighbour-chunk expansion** | **87%** | **83%** | **Live** |
| v10 | Tool-calling agent | 91% | 74% | Experiment |

---

## 6. Key decisions (replaces "Highlights", keep the tick icons)

- **Replaced a misleading 94% with an honest evaluation.** The real baseline was 26%; ingestion was saving placeholder lines instead of code.
- **Found the real bottleneck by reading the failures.** The right page was retrieved, but the code sat in the next chunk. Neighbour expansion took correctness from 61% to 87%, the first change where both metrics went up.
- **Rejected two popular techniques on data.** Hybrid search and four cross-encoder rerankers were built and measured. Both made answers worse, so neither shipped.
- **Built a tool-calling agent, then kept the simpler pipeline.** A hand-written tool loop on the Claude API reached perfect retrieval and 91% correct, but invented more (faithfulness 74%) at ~1.4× the cost and ~2× the latency.
- **Put rules in code, not the prompt.** Three prompt versions couldn't stop the agent from refusing without searching; forcing the first call to be a search fixed it in one line.
- **Shipped like a real service.** Docker, deployed on Render, per-IP rate limiting.

---

## 7. Tech stack (badges)

Python · FastAPI · ChromaDB · Sentence-Transformers (local embeddings) · Claude Haiku (answers) · Claude Sonnet (judge) · LLM-as-judge evaluation · Tool-calling agent · Docker · Render

(Keep any existing badges that are still true; drop any that aren't used.)

---

## 8. Limitations & next (small section, builds trust)

**Known limitations**
- Comparison questions (e.g. FastAPI vs Flask) still fail: the docs don't compare directly.
- 23 answerable test questions is small: one question ≈ 4%, so ±2 is noise.

**Next**
- A verification step that checks every code line in the answer against the source.
- A larger eval set (50–100 questions).

---

## 9. Sidebar / about

- **Name:** Vivek Gupta
- **Title:** Backend & AI Engineer
- **Short bio:**
  Backend engineer with about 4 years of experience in C#/.NET, Node.js and SQL. Most recently the sole backend engineer at PPI Advisory in Toronto. Now building AI systems the same way I build backends: measured, tested and honest about what works.
- **Location:** Delhi, India · Open to remote
- **Links:** Email (Vivek.GuptaVG@outlook.com) · LinkedIn (https://linkedin.com/in/guvivek) · GitHub (https://github.com/VivekGupta1999) · Resume (/resume.pdf)

---

## 10. Chat widget

**Intro line (empty state):** Ask a question about FastAPI. Answers come only from the official docs.

**Example buttons (exactly 3):**
1. How do I add CORS middleware?
2. My signup endpoint is slow because it sends an email. Can I respond first?
3. How do I set up routing in Django? *(should be refused)*

**Behaviour:**
- If the answer starts with "I don't know", show no sources, just: "No sources: the docs don't cover this."
- Sources become clickable links to the live docs:
  `fastapi-repo/docs/en/docs/tutorial/cors.md` → `https://fastapi.tiangolo.com/tutorial/cors/`
  (strip `fastapi-repo/docs/en/docs/`, drop `.md`, add `/`; `index.md` maps to its folder). Link text = short path, open in new tab.
- Small footnote under the input: "Limited to 5 questions per minute. Powered by Claude Haiku."

---

## 11. Footer

Built by Vivek Gupta · [GitHub](https://github.com/VivekGupta1999/rag-docs-assistant) · [LinkedIn](https://linkedin.com/in/guvivek)
