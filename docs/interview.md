# RailNiyam — Interview Preparation Guide

## 1. 60-Second Pitch

> "Over 24 million passengers travel on Indian Railways every day, yet when plans change or trains are delayed, they face a confusing mix of 2015 Ministry of Railways Gazette notifications, zonal circulars, and IRCTC TDR rules. Cancelling at 47 hours versus 49 hours can mean losing 25% of the fare instead of a flat ₹180 fee—and outdated 2013 PDFs still circulating online make it worse.
>
> **RailNiyam** is a production-ready, citation-grounded AI assistant and refund calculator built with **FastAPI**, **ChromaDB**, **LangGraph**, and **Streamlit**. Every policy answer is retrieved from verified 2015 rules with explicit citations, while actual rupee deductions are computed deterministically in Python—never guessed by an LLM. For sensitive actions like confirming a refund calculation, a LangGraph state machine enforces a human-in-the-loop approval gate.
>
> Across our 15-question evaluation benchmark, RailNiyam achieved a **93.3% retrieval hit rate**, **100% answer accuracy**, sub-2.5 ms cached responses, and 100% 'I don't know' compliance on out-of-domain queries—backed by 19 automated tests, CI/CD, and Docker deployment."

*(~155 words — ~55–60 seconds at a steady speaking pace.)*

---

## 2. Interview Story: The Hardest Problem (Versioned Rules)

### Situation
When building RailNiyam, I discovered a critical data-integrity hazard: **conflicting, versioned railway rules still coexist on the web.** Specifically, the **2013 IRCTC PDF** (which lists old flat charges of **₹60 / ₹90 / ₹120** and a **6-hour** cancellation slab) is still indexed online alongside the **Ministry of Railways / SCR Gazette rules effective 12.11.2015** (which doubled flat minimums to **₹120 / ₹180 / ₹240** and introduced **48h–12h (25%)**, **12h–4h (50%)**, and **<4h (0% refund)** slabs), while newer circulars also govern Tatkal and TDR rules.

### Task
If a passenger asks *"How much will I lose if I cancel my Sleeper ticket 6 hours before departure?"*, an ungrounded LLM—or a RAG bot indexing mixed-vintage PDFs—can easily hallucinate the obsolete 2013 ₹60/₹120 figures or do wrong percentage math. The system had to:
1. Strictly enforce the **latest verified rule** and display the **rule reference and effective date** (`w.e.f. 12.11.2015`).
2. **Compute refunds with deterministic code** rather than letting the LLM guess numbers.
3. Refuse to guess when asked about dynamic data outside the rules (like exact bank credit arrival dates).

### Action
1. **Curated Version-Tagged Knowledge Base (`data/records.json`)**: I structured all 18 official cancellation and TDR rules into verified JSON records, each tagged with `rule_ref` (e.g., `SCR Refund Rules w.e.f. 12.11.2015, Rule 2(iii)`), `source_url`, and `verified: true`, eliminating stale 2013 PDFs from the index.
2. **Deterministic Python Calculator (`app/tools.py`)**: I separated *policy retrieval* from *arithmetic*. `rail_refund_calculator()` encodes the exact 2015 `FLAT_MINIMUM_CHARGES` (`1A/EC: ₹240`, `2A/FC: ₹200`, `3A/CC/3E: ₹180`, `SL: ₹120`, `2S: ₹60`), the `48h / 12h / 4h` percentage slabs (`max(percentage, flat_min)`), confirmed Tatkal zero-refund, and RAC/WL ₹60 clerkage (`₹30` for `2S`) up to 30 minutes before departure.
3. **Citation-Grounded RAG & Guardrails (`app/rag.py`)**: The prompt requires `[Source: <source>, Page <page>]` citations and forces an explicit `"I don't know"` response when context is missing or when `UNANSWERABLE_PATTERNS` (e.g., bank credit timelines) are detected.
4. **Interactive Proof in the UI (`ui/app.py`)**: I built the **"Cancel now or later?" Live Refund Simulator**, letting users drag a departure-hours slider to see exact rupee deductions and the cited 2015 rule update in real time.

### Result
- **0% arithmetic hallucination** on refund calculations—every rupee figure comes from unit-tested Python code (`tests/test_tools.py`).
- **100% answer accuracy** and **100% citation grounding** across our 15-question `eval/eval_set.json` benchmark.
- Every response clearly surfaces the `w.e.f. 12.11.2015` rule reference so passengers can trust the numbers.

---

## 3. Answers to 10 Likely Interview Questions

### Q1. Why use RAG + a deterministic Python calculator instead of just prompting an LLM?
**Answer:** LLMs are probabilistic text generators—they are unreliable at multi-step conditional arithmetic (e.g., `max(25% of fare, flat minimum × passengers)`) and can blend outdated 2013 training-data numbers with 2015 rules. By using **RAG** (`app/rag.py`) strictly for retrieving and citing policy text, and **Python code** (`rail_refund_calculator` in `app/tools.py`) for all rupee calculations, we get natural-language understanding without sacrificing financial accuracy.

### Q2. How do you prevent the LLM from hallucinating or answering out-of-domain questions (like bank refund timelines)?
**Answer:** We enforce three layers of defense in `app/rag.py`:
1. **Pattern Guard (`is_unanswerable_query`)**: Known out-of-domain queries—such as *"in how many days will the exact amount credit to my bank account"* (our Q6 test case)—immediately return an explicit `"I don't know"` response explaining that bank settlement timelines are not in the rules database.
2. **Strict System Prompt**: `build_rag_prompt()` instructs the model to answer *only* from retrieved chunks, include `[Source: ..., Page ...]` citations, and start with `"I don't know"` if context is insufficient.
3. **Prompt-Injection Shield (`is_prompt_injection`)**: Regex signatures block jailbreak attempts like *"ignore previous instructions"* or *"reveal your system prompt"*, verified by `tests/test_security.py`.

### Q3. How does your search work—why have both TF-IDF (`SmartSearch`) and ChromaDB (`vectorstore.py`)?
**Answer:** They solve complementary retrieval problems:
- **`SmartSearch` (`app/smart_search.py`)** uses `scikit-learn` TF-IDF + cosine similarity. It is ultra-fast (<1 ms) and excels at exact railway terms like `"3A"`, `"Tatkal"`, or `"Rule 2(ii)"`.
- **`ChromaDB` (`app/vectorstore.py` + `app/embed.py`)** stores chunked rules as dense embeddings (`RailNiyamEmbeddingFunction`), capturing semantic intent even when a passenger uses everyday phrasing (e.g., *"missed my train because it was late"* $\rightarrow$ TDR rule).

### Q4. How did you evaluate the RAG pipeline, and what did the benchmark show?
**Answer:** We built `eval/eval_set.json` with **15 evaluation questions** (including unanswerable Q6) and ran `eval/run_eval.py` comparing two retrieval configurations:
- **Config A (`top_k=2`, tight)**: 93.3% retrieval hit rate, 100.0% answer accuracy.
- **Config B (`top_k=4`, broad)**: 93.3% retrieval hit rate, 100.0% answer accuracy.
We chose `top_k=3` as the default in `AskRequest` (`app/main.py`) to balance broad context coverage with low prompt token usage (~192 prompt tokens on average).

### Q5. Why did you use LangGraph for `/agent`, and how does the Human-in-the-Loop approval gate work?
**Answer:** In `app/graph.py`, a linear chain isn't enough when an assistant needs memory, conditional tool routing, and confirmation before confirming a cancellation/refund action. I modeled the workflow as a LangGraph `StateGraph` with `MemorySaver` checkpointing keyed by `thread_id`:
1. `router_node` extracts fare/class/status/hours via `extract_calculation_params()`.
2. If calculation parameters are present and `approve` is not yet `True`, it routes to `approval_node`, sets `status="waiting_for_approval"`, and pauses.
3. On the next turn (same `thread_id`) with `approve: true` (or `"Yes"`), `router_node` routes to `calculate_node`, executes `rail_refund_calculator`, and returns the exact breakdown. If rejected, it routes to `rejection_node`.

### Q6. How did you optimize latency and token costs in production?
**Answer:** I implemented an in-memory LRU `QUERY_CACHE` and `estimate_tokens()` telemetry in `app/cache.py`, wired directly into `POST /ask` in `app/main.py`:
- **Cache Hit**: Returns the stored answer and citations in **1.8 ms – 2.4 ms** with **0 LLM tokens consumed (100% token savings)**.
- **Cache Miss**: Logs `latency_ms`, `prompt_tokens` (~192), `completion_tokens` (~84), and `total_tokens` (~276), then caches the response.
- **Cache Controls**: Exposed `GET /cache/stats` (hits, misses, hit rate %) and `DELETE /cache` for operational visibility and cache invalidation.

### Q7. How do you protect the API against abuse and malformed inputs?
**Answer:** Every endpoint enforces strict schema validation via Pydantic v2 in `app/main.py`:
- `AskRequest`: `question` must be `3–500` characters, `top_k` must be `1–10`.
- `AgentRequest`: `message` is capped at `1000` characters, `thread_id` at `100` characters.
- Combined with `is_prompt_injection()` in `app/rag.py`, oversized or adversarial payloads are rejected with `HTTP 400`/`422` or neutralized before ever reaching an LLM.

### Q8. What happens if the external LLM API key is missing or the provider goes down?
**Answer:** RailNiyam degrades gracefully without crashing:
- In `app/rag.py`, `answer_question()` catches provider/key errors and falls back to `synthesize_offline_answer()`, which formats a deterministic, citation-backed answer directly from the top retrieved rule chunks.
- In `app/main.py`, `POST /chat` catches `OSError` and returns a structured `ChatResponse` built from `ENGINE.search()`'s top TF-IDF match.
This also allows our full 19-test `pytest` suite and local demos to run reliably offline.

### Q9. How is RailNiyam tested, containerized, and deployed?
**Answer:**
- **Testing & Linting**: 19 automated tests across `tests/test_records.py`, `tests/test_search.py`, `tests/test_tools.py`, `tests/test_agent.py`, `tests/test_api.py`, and `tests/test_security.py`, plus `ruff check .` for linting.
- **CI/CD**: `.github/workflows/ci.yml` runs `ruff`, `pytest`, and a `docker build` check on every push/PR.
- **Deployment**: Packaged in a `Dockerfile` using `entrypoint.sh`, which runs FastAPI (`uvicorn`) internally on `127.0.0.1:8000` and serves the Streamlit UI (`ui/app.py`) publicly on `$PORT` for Render deployment.

### Q10. What would you improve next if you had two more weeks?
**Answer:** Three concrete upgrades:
1. **Automated Circular Diffing**: A scheduled ingestion job in `app/fetch.py` / `app/ingest.py` to detect new Ministry of Railways / IRCTC circulars by effective date and automatically deprecate superseded records.
2. **Persistent Checkpointer**: Swap LangGraph's in-memory `MemorySaver` for a SQLite or Postgres checkpointer so agent approval threads survive container restarts.
3. **Multilingual Support**: Add Hindi and regional language query translation before retrieval so non-English-speaking passengers can use RailNiyam directly.

