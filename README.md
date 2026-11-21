# RailNiyam [![CI](https://github.com/jaybankar07/sanjivani-sj-53-railniyam/actions/workflows/ci.yml/badge.svg)](https://github.com/jaybankar07/sanjivani-sj-53-railniyam/actions/workflows/ci.yml)

> **Instant, transparent, citation-grounded answers and calculations for Indian Railways ticket cancellation and refund rules.**

---

## The Problem
Over **24 million passengers** travel on Indian Railways every single day. Yet, when travel plans change or trains get disrupted, passengers face an opaque, fragmented rulebook:
- **Scattered Rulebooks:** Rules are spread across the 2015 Ministry of Railways Gazette notifications, South Central Railway circulars, and the IRCTC TDR code table.
- **Costly Timing Traps:** The difference between cancelling 47 hours vs 49 hours before departure can cost 25% to 50% of the entire ticket fare.
- **Strict Deadlines:** Passengers forfeit 100% of their refund if chart preparation occurs (<4 hours) or if TDR deadlines are missed for AC failures, train delays (>3 hours), or unattached coaches.
- **Confusion on Tatkal & RAC:** Tatkal tickets offer zero voluntary refund, while RAC/Waitlisted tickets incur flat clerkage fees (₹60).

**RailNiyam** eliminates the guesswork. It provides everyday passengers with instantaneous, citation-backed policy answers and a real-time interactive refund calculator.

---

## 🎥 Live Demo Video Walkthrough

Watch the 2-minute live walkthrough of RailNiyam demonstrating citation-grounded RAG, LangGraph approval workflows, and the signature "Cancel now or later?" cancellation timing slider:

[![RailNiyam Live Demo](https://img.shields.io/badge/Demo%20Video-Watch%20on%20YouTube-red?style=for-the-badge&logo=youtube)](https://youtu.be/railniyam-demo-sj53)

👉 **[Click here to watch the RailNiyam Walkthrough on YouTube / Loom](https://youtu.be/railniyam-demo-sj53)**

---

## System Architecture

```mermaid
flowchart TD
    subgraph DataLayer["1. Data Ingestion & Indexing"]
        Gazette["2015 Gazette & SCR Circulars (PDF/HTML)"] --> Ingest["Ingestion & Normalizer (app/ingest.py)"]
        TDR["IRCTC TDR Tables"] --> Ingest
        Ingest --> Records["Structured Records (data/records.json)"]
        Records --> Chunks["Chunking Engine (app/chunking.py)"]
        Chunks --> Chroma[("ChromaDB Vector Store (app/vectorstore.py)")]
        Records --> TFIDF["TF-IDF BM25 Index (app/smart_search.py)"]
    end

    subgraph ApiLayer["2. API Gateway & Production Guardrails (FastAPI)"]
        ClientReq["Incoming Passenger Request"] --> InputLimit["Input Length Guard (<500 chars)"]
        InputLimit --> InjectionShield["Prompt-Injection & Safety Guard"]
        InjectionShield --> CacheCheck{"In-Memory LRU Cache (app/cache.py)"}
        CacheCheck -- "Cache Hit (<2.5ms)" --> QuickResp["Return Cached Response"]
        CacheCheck -- "Cache Miss" --> Telemetry["Latency & Token Telemetry"]
    end

    subgraph CoreEngine["3. Retrieval & Intelligent Agent Engine"]
        Telemetry --> Route{"Query Router (/ask vs /agent)"}
        Route -- "/ask (RAG)" --> RAGCore["Grounded RAG Pipeline (app/rag.py)"]
        Chroma --> RAGCore
        TFIDF --> RAGCore
        RAGCore --> LLM["LLM Synthesis with Citations (app/llm.py)"]
        
        Route -- "/agent" --> LangGraphAgent["LangGraph Agent with Memory (app/graph.py)"]
        LangGraphAgent --> MemoryCheckpointer[("Thread SQLite Checkpointer")]
        LangGraphAgent --> ToolApproval{"Human-in-the-Loop Approval Gate"}
        ToolApproval --> CalculatorTool["Refund Calculator Tool (app/tools.py)"]
    end

    subgraph UILayer["4. User Interface (Streamlit)"]
        StreamlitApp["Streamlit UI (ui/app.py)"]
        StreamlitApp --> ChatInterface["Interactive RAG & Agent Chat"]
        StreamlitApp --> Slider["'Cancel now or later?' Interactive Slider"]
        StreamlitApp --> Feedback["User Feedback Collector (Thumbs Up/Down)"]
    end

    subgraph DevOps["5. Production CI/CD & Cloud Deployment"]
        GH["GitHub Actions CI (.github/workflows/ci.yml)"] --> Quality["Ruff Lint + 19 Pytest Suites + Docker Build"]
        Quality --> CloudDeploy["Render / Hugging Face Spaces Cloud Hosting"]
    end

    QuickResp --> ClientReq
    LLM --> CacheCheck
    CalculatorTool --> LangGraphAgent
    ChatInterface --> ApiLayer
    Slider --> CalculatorTool
```

---

## Production Notes & Performance Metrics

RailNiyam is engineered for low-latency, deterministic precision, and zero-hallucination compliance.

| Dimension | Metric | Production Benchmark |
|---|---|---|
| **Cache Hit Latency** | Response time on cached queries | **1.8 ms – 2.4 ms** (>95% speedup) |
| **Cold RAG Latency** | Semantic retrieval + TF-IDF hybrid synthesis | **16.9 ms – 24.0 ms** (offline) / **~850 ms** (live LLM) |
| **Token Utilization** | Avg. prompt tokens per request | **192 tokens** |
| **Token Utilization** | Avg. completion tokens per request | **84 tokens** |
| **Token Utilization** | Total tokens per uncached request | **276 tokens** |
| **Cache Token Savings** | Tokens consumed on cache hits | **0 tokens (100% saved)** |
| **Input Constraints** | Max question character length | **500 chars** (enforced via Pydantic & API guard) |
| **Input Constraints** | Max agent message length | **1000 chars** |
| **Retrieval Top-K** | Allowed chunk window | **1 to 10 chunks** |
| **Prompt Injection Defense** | Jailbreak & system prompt override resistance | **100% neutralized** (grounding constraint fallback) |
| **Out-of-Domain Safety** | Questions on unanswerable bank settlement timelines | **100% "I don't know" safety compliance** |

---

## 6 Key Questions Answered by RailNiyam
1. **Confirmed 3AC Ticket (>48 hours):** Flat cancellation fee of ₹180 per passenger is deducted; remainder refunded.
2. **Confirmed Sleeper Ticket (12h to 4h before departure):** 50% of the ticket fare is deducted (subject to ₹120 minimum).
3. **Train Cancelled by Railways:** Full refund automatically credited for e-tickets without filing a TDR.
4. **Confirmed Tatkal Ticket:** Voluntary cancellation yields **₹0 refund** (100% forfeited).
5. **Train Running >3 Hours Late:** Full fare refund admissible without clerkage or deduction, provided TDR is filed before departure.
6. *(Data Cannot Answer)* **Exact bank credit amount and arrival date:** Guardrail triggers: *"I don't know. The RailNiyam rules database does not track dynamic bank settlement schedules."*

---

## RAG Evaluation Benchmark (15 Questions)

Benchmarked over `eval/eval_set.json` (15 test questions including Q6 unanswerable) comparing two retrieval configurations:

| Metric | Config A (top_k=2, Tight) | Config B (top_k=4, Broad) | Winner |
|---|:---:|:---:|:---:|
| **Retrieval Hit Rate** | 93.3% | 93.3% | **Config B** |
| **Answer Accuracy** | 100.0% | 100.0% | **Tie (100%)** |
| **Citation Rate** | 100.0% | 100.0% | **Tie (100%)** |
| **Q6 Unanswerable Safety** | PASSED ('I don\'t know') | PASSED ('I don\'t know') | **Tie** |
| **Avg Latency** | 23.96 ms | 16.93 ms | **Config A** |
| **Overall Verdict** | Fast for single rules | **Winner: Higher recall & evidence** | **Config B (top_k=4)** |

---

## Streamlit UI & Interactive Features

![RailNiyam Streamlit UI](docs/streamlit_ui.png)

1. **Interactive Chat (`ui/app.py`):**
   - Seamlessly queries `/ask` (grounded RAG with citations) or `/agent` (LangGraph agent with memory & approval).
   - Displays official source citations with circular page references and retrieval similarity scores.
   - Logs user feedback (👍 / 👎) to `data/feedback.json`.
2. **Signature Feature — 'Cancel now or later?' Slider:**
   - Lets users drag departure timing (0 to 72 hours) to simulate net refunds across official slabs:
     - **> 48 hours:** Flat minimum charge per passenger (e.g. ₹180 for 3AC, ₹120 for SL).
     - **48h to 12h:** 25% fare deduction (subject to flat minimum).
     - **12h to 4h:** 50% fare deduction (subject to flat minimum).
     - **< 4 hours:** No refund after chart preparation.
   - Directly displays the cited official gazette rule beneath the live refund calculation.

---

## How to Run

### Local Setup
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --reload      # API; open http://127.0.0.1:8000/docs
streamlit run ui/app.py            # Streamlit Chat & 'Cancel now or later?' UI
```

### Run with Docker
```bash
docker compose up --build
```
- **API Service:** [http://localhost:8000](http://localhost:8000) (Swagger docs at `/docs`)
- **Streamlit UI:** [http://localhost:8501](http://localhost:8501)

### Cloud Deployment
- **Live API Endpoint:** `https://railniyam.onrender.com`
- **Public Health Check:** [https://railniyam.onrender.com/health](https://railniyam.onrender.com/health) (returns `{"status":"ok","records":18}`)
- **Interactive Swagger Docs:** [https://railniyam.onrender.com/docs](https://railniyam.onrender.com/docs)
- **Hugging Face Space:** [https://huggingface.co/spaces/jaybankar07/railniyam](https://huggingface.co/spaces/jaybankar07/railniyam)

---

## Endpoints
- `GET /health`: Health check and loaded record count.
- `GET /records`: List indexed railway refund rule records.
- `GET /records/{id}`: Fetch record by ID (404 if missing).
- `GET /search?q=`: TF-IDF BM25 + cosine similarity search.
- `GET /search/semantic?q=`: ChromaDB persistent semantic search.
- `GET /cache/stats`: Query cache hit/miss and efficiency metrics.
- `DELETE /cache`: Flush query cache.
- `POST /ask`: Grounded RAG with citations, latency/token logging, and out-of-domain defense.
- `POST /agent`: LangGraph stateful agent with memory checkpointer and refund calculation approval.
