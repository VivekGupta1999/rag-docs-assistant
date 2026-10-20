# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A RAG question-answering assistant over the FastAPI documentation. The chatbot itself is secondary — the
point of the project is the **evaluation harness** and the sequence of measured versions (v1–v10) it drove,
documented in detail in `README.md`. Any change to retrieval, chunking, or prompting should be justified by
running the eval, not by intuition — that's the whole premise of the repo.

## Commands

Setup:
```bash
pip install -r requirements.txt
# needs ANTHROPIC_API_KEY in .env
```

Run the eval harness (writes `results/<tag>_<timestamp>.json`):
```bash
python -c "from eval_runner import run_eval; run_eval('v9')"                  # generate.py pipeline (live)
python -c "from eval_runner import run_eval; run_eval('v10', mode='agent')"   # agent.py pipeline (experiment)
```

Judge a results file for correctness + faithfulness (set `RESULTS_FILE` / `JUDGED_FILE` constants at the top
of `judge.py` first — they're hardcoded paths, not CLI args):
```bash
python judge.py
```

Free retrieval-only checks (no API calls):
```bash
python retrieval_check.py   # vector vs. hybrid hit@5 and MRR over the eval set
python query_test.py        # one-off manual ChromaDB query
```

Try the agent manually on two sample questions:
```bash
python agent.py
```

Rebuild the vector DB from the FastAPI docs source (destructive — drops and recreates the `fastapi_docs`
collection in `./chroma_db`; requires `fastapi-repo/` checked out locally, which is gitignored):
```bash
python ingest.py
```

Run the FastAPI server locally:
```bash
uvicorn main:app --reload
```

There is no test suite, linter, or formatter configured — evaluation correctness is checked via the eval
harness above, not unit tests.

## Architecture

**Pipeline:** `ingest.py` → ChromaDB (`./chroma_db`, persistent, collection `fastapi_docs`) → `generate.py`
(or `agent.py`) → `main.py` (FastAPI endpoint) → `static/index.html` (single-page frontend with a floating
chat widget).

**Ingestion (`ingest.py`)**
- Reads FastAPI's own docs (`fastapi-repo/docs/en/docs/*.md`, a checkout of the upstream repo — not tracked
  in git).
- `inline_code_includes`: the docs reference external code samples via `{* ../../docs_src/... *}` tags;
  these are resolved and the real code is inlined before chunking. This was the fix for the very first
  (wrong) measurement — the baseline was indexing the literal include tag instead of the code.
- `split_sections` / `chunk_page`: heading-aware chunking that labels each chunk `Page Title > Section
  Title` and never splits inside a fenced code block (tracked via a running backtick-fence parity count).
- `doc_type` metadata (`guide` / `reference` / `changelog`) is set per chunk from the file path; retrieval
  filters to `doc_type == "guide"` only, excluding changelog and auto-generated API reference pages.
- Chunk IDs are positional (`chunk_0`, `chunk_1`, ...) in file order — this ordering is load-bearing, see
  neighbour expansion below.

**Retrieval / generation (`generate.py`, live path — v9)**
- `RETRIEVAL` module-level constant switches between `"vector"` (live) and `"hybrid"` (rollback switch to
  the experiment in `hybrid.py`, not shipped).
- Vector query, top 5 chunks, filtered to `doc_type: "guide"`.
- **Neighbour expansion (`expand`)**: the key change that took correctness from 61% to 87%. Each retrieved
  chunk's numeric ID is used to pull the chunk immediately before and after it (`WINDOW = 1`) *on the same
  source page*, then chunks from the same page are joined in ID order. Rationale: questions are phrased in
  prose and match prose chunks, but the matching code sample usually lives in the adjacent chunk. This
  depends on ingestion's chunk IDs being contiguous per-page in file order.
- Generation is Claude Haiku (`claude-haiku-4-5-20251001`), `temperature=0`, with a grounding rule in
  `SYSTEM_PROMPT`: only use code/parameters/values that literally appear in the context, and say "I don't
  know" when the context doesn't cover the question.

**Hybrid search experiment (`hybrid.py`, not shipped — do not wire into the live path without re-running
the eval)**
- BM25 (`rank_bm25`) over all guide chunks + vector search, deduped into a candidate pool, reranked with a
  cross-encoder (`fastembed`, `Xenova/ms-marco-MiniLM-L-12-v2`), capped at 3 results per source page.
- Improved page-ranking metrics (MRR 0.77→0.86) but *worse* final answers (correctness 14→11/23) — kept as
  a documented negative result, not deleted. Needs `pip install rank-bm25 fastembed` (not in the default
  `requirements.txt` install path for the live app).

**Agent experiment (`agent.py`, v10 — not shipped, `generate.py`/v9 stays live)**
- Hand-rolled tool-use loop against the Claude API (no agent framework): `search_docs(query)` (same
  retrieval + neighbour-expansion as `generate.py`) and `read_page(source)` (full page, truncated at
  `MAX_PAGE_CHARS = 6000`).
- Capped at `MAX_STEPS = 5` rounds. Tool exceptions are caught and returned to the model as text, not
  raised. The first round forces `tool_choice: {"type": "any"}` so the model can't refuse without
  searching — three prompt-only attempts failed to prevent that; this one-line fix did.
- Returns `(answer, sources, trace, context)` where `context` is the literal concatenation of everything
  the tools returned — this is what the faithfulness judge checks the agent's answer against (not a
  fresh `get_context` call, since the agent may have made multiple/different tool calls than a single
  retrieval would).
- Better retrieval (100% hit) and fixes multi-part questions, but lower faithfulness than v9 (74% vs 83%):
  it stitches code across pages and fills gaps on truncated `read_page` reads. Also ~1.4× cost, ~2×
  latency. This is why v9, not v10, is live.

**Evaluation (`eval_set.py`, `eval_runner.py`, `judge.py`, `retrieval_check.py`)**
- `eval_set.py`: 31 hand-written `EvalCase`s with a `category` (`direct` / `paraphrased` / `multi_doc` /
  `near_miss` / `out_of_scope`), `expected_sources` (substrings of the doc file path), `should_answer`, and
  hand-verified `key_facts` a correct answer must contain. `multi_doc` cases require *all* expected sources
  to be retrieved; other categories require *any*.
- `eval_runner.run_eval(tag, mode)`: runs every case through either `generate.answer_question` (`mode`
  anything but `"agent"`) or `agent.ask_agent` (`mode="agent"`), checks retrieval hit and a crude
  string-match refusal check, and writes the full results (including the agent's trace/context when
  applicable) to `results/<tag>_<timestamp>.json`.
- `judge.py`: a second pass over a results file using Claude Sonnet as an LLM judge with forced tool use
  (`tool_choice` pinned to a specific tool) for two structured verdicts — `record_correctness` (per-key-fact
  present/absent) and `record_faithfulness` (list of unsupported claims). Faithfulness is checked against
  the agent's actual recorded tool output when present (`r["context"]`), otherwise against a freshly
  rebuilt `get_context(question)` (same chunks v1–v9 would have seen). Verdicts are cached in `JUDGED_FILE`
  keyed by whether the facts/answer/context are unchanged, so re-running only pays for what changed.
  `RESULTS_FILE` / `JUDGED_FILE` are constants at the top of the file — edit them before each run, they are
  not derived from `eval_runner`'s output filename automatically.
- `retrieval_check.py`: free (no LLM calls) vector-vs-hybrid comparison — hit@5 and MRR per case, with a
  per-case diff flag when one retrieval method hits and the other misses.
- Only the 23 `should_answer=True` cases count toward "Correct"/"Faithful" scores in the README; all 31
  (including refusal cases) count toward "Retrieval" and "Behaviour".

**Serving (`main.py`)**
- `GET /` serves `static/index.html`; `GET /resume.pdf` serves `readme_assets/Resume.pdf`.
- `POST /query` calls `generate.answer_question` directly (the live v9 pipeline, not the agent) and is rate
  limited to 5/minute per IP via `slowapi`, keyed off `X-Forwarded-For` (`get_real_client_ip`) since the
  deployment sits behind Render's proxy — don't key straight off `get_remote_address` or rate limiting
  becomes effectively per-proxy instead of per-client.
- Deployed via the included `Dockerfile` (python:3.12-slim, `uvicorn main:app`) on Render.

## Working in this repo

- `generate.py`'s `RETRIEVAL` constant and `hybrid.py` are intentionally live code paths for comparison, not
  dead code — don't delete `hybrid.py` or "clean up" the switch without checking the README's results table
  first.
- Any retrieval/prompt/chunking change should be validated by re-running `eval_runner.run_eval` +
  `judge.py` and comparing against the README's results table before being called an improvement — a single
  question is ~4% of the 23-question answerable set, so treat ±1 question as noise, per the README's own
  caveat.
- `fastapi-repo/` (the upstream FastAPI docs checkout `ingest.py` reads from) and `chroma_db/` (the
  committed, pre-built vector DB) are both gitignored/present locally but not meant to be regenerated
  casually — `chroma_db/` is deployed as-is.


## Rules
- Don't change backend files (main.py, generate.py, agent.py, ingest.py, eval files) unless asked.
- Never run eval_runner.py or judge.py without asking: they call the paid API.
- Git root is the PARENT folder. Never `git add .` or `git add -A`; add files by name.
- Never commit chroma_db/chroma.sqlite3; restore it with `git restore`.
- Keep static/index.html a single self-contained file, keep the existing style.
- Show diffs and explain before committing. Don't push unless asked.