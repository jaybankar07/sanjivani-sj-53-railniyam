# RailNiyam — Project Progress Tracker

All 14 days of the RailNiyam build, evaluation, hardening, deployment, and interview preparation are **complete**.

---

## Week 1: Data, Search & API Foundation

- [x] **Day 1 — Project Setup & Problem Card**: Initialized repository, `.gitignore`, `README.md` with 6 core passenger questions, and CLI exploration scripts (`day01_intro.py`, `day01_menu.py`).
- [x] **Day 2 — Domain Dataset & CLI**: Curated 18 verified Indian Railways refund & TDR rules (`data/sample_records.py`), refactored into `app/records.py` and `app/cli.py`, and added `requirements.txt`.
- [x] **Day 3 — Official Ingestion Pipeline**: Created `Record` dataclass (`app/models.py`), `app/fetch.py` (HTTP fetching with timeouts and error handling), and `app/ingest.py` generating `data/records.json` with `rule_ref` (`w.e.f. 12.11.2015`) and `source_url`.
- [x] **Day 4 — FastAPI Backend & TF-IDF Search**: Built `app/main.py` (`GET /health`, `/records`, `/records/{record_id}`, `/search`, `POST /questions`), `app/smart_search.py` (TF-IDF + cosine ranking), and `analysis/explore.py`.
- [x] **Day 5 — Checkpoint 1**: Authored `docs/how_llms_work.md` with Mermaid architecture diagram and `docs/questions.md` (10 real RailNiyam questions including Q6 out-of-domain test); tagged `checkpoint-1`.

## Week 2: LLM, RAG, Agents & UI

- [x] **Day 6 — LLM Wrapper & Prompt Versioning**: Built `app/llm.py` (Groq/Gemini wrapper + JSON parsing), `prompts/` (`system.txt`, `task_v1.txt`, `task_v2.txt`), `POST /chat`, `.env.example`, and `eval/prompt_compare.md`.
- [x] **Day 7 — Chunking, Embeddings & Vector Store**: Implemented `app/chunking.py`, `app/embed.py`, persistent ChromaDB collection in `app/vectorstore.py`, `GET /search/semantic`, and `eval/search_results.md`.
- [x] **Day 8 — Grounded RAG & Benchmark**: Built `app/rag.py` + `POST /ask` with citations and Q6 `"I don't know"` safety; benchmarked 15 questions in `eval/eval_set.json` via `eval/run_eval.py` (93.3% hit rate, 100% answer accuracy).
- [x] **Day 9 — Deterministic Calculator & LangGraph Agent**: Implemented `rail_refund_calculator` in `app/tools.py`, parameter extraction in `app/agent_loop.py`, and stateful LangGraph `StateGraph` with `MemorySaver` + Human-in-the-Loop approval gate in `app/graph.py` (`POST /agent`).
- [x] **Day 10 — Checkpoint 2 (Streamlit UI)**: Built `ui/app.py` with RAG/Agent chat, citation display, thumbs up/down feedback, and the signature **"Cancel now or later?"** live refund simulator slider; tagged `checkpoint-2`.

## Week 3: Testing, CI/CD, Hardening & Final Delivery

- [x] **Day 11 — Automated Testing, Linting & Docker**: Added `tests/` (unit, search, tools, agent, API tests), configured `ruff` linting, and created `Dockerfile` and `docker-compose.yml`.
- [x] **Day 12 — CI/CD & Cloud Deployment**: Added `.github/workflows/ci.yml` (`ruff`, `pytest`, `docker build`), CI badge in `README.md`, and Render deployment configuration (`entrypoint.sh`).
- [x] **Day 13 — Production Hardening & Observability**: Added `app/cache.py` (`QUERY_CACHE` + token estimation), `GET /cache/stats`, `DELETE /cache`, input length guards (500/1000 chars), prompt-injection tests (`tests/test_security.py`), production metrics & Mermaid diagram in `README.md`, `docs/resume.md`, and `docs/project_banner.html`.
- [x] **Day 14 — Final Polish, Interview Prep & Tagging**:
  - [x] Wrote `docs/interview.md` with 60-second pitch, versioned-rules (2013 vs 2015) hardest-problem story, and 10 technical Q&As.
  - [x] Created `PROGRESS.md` and closed every open item.
  - [x] Rehearsed the live demo twice (verified `/health`, `/ask` RAG + Q6 guardrail, `/agent` approval gate + `rail_refund_calculator`, and full `pytest` + `ruff` suite).
  - [x] Committed changes with `day-14:` prefix, created `final` tag, and pushed to `origin/master`.

