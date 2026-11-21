# RailNiyam — Resume Bullets

These 3 high-impact, quantified, ATS-friendly resume bullets highlight the engineering achievements, AI systems architecture, and production readiness of the **RailNiyam** project.

---

### 1. Production RAG Architecture & Grounded Retrieval
- **Architected a production RAG system** for Indian Railways refund policies utilizing persistent **ChromaDB** vector storage and **TF-IDF BM25** hybrid retrieval, achieving a **93.3% retrieval hit rate**, **100% citation grounding**, and sub-20ms search latency across official Ministry of Railways gazette circulars, with automated "I don't know" safeguards against hallucinated bank settlement estimates.

### 2. LangGraph Autonomous Agent & Deterministic Calculation Engine
- **Engineered an autonomous conversational agent with LangGraph**, featuring persistent thread-level memory checkpointers, human-in-the-loop approval gates for refund actions, and a deterministic Python refund engine accurately evaluating 100% of official 2015 gazette cancellation slabs (>48h flat minimum, 25%, 50%, confirmed Tatkal zero-refund, and RAC/WL clerkage fees).

### 3. Full-Stack UI, Performance Engineering & CI/CD Automation
- **Developed a full-stack AI application** with a Streamlit interface featuring real-time "Cancel now or later?" deduction slider simulations; hardened the FastAPI backend with in-memory LRU caching (**<2.5ms cache-hit response**, 100% token savings), prompt-injection defenses, request telemetry, and an automated GitHub Actions CI/CD pipeline running 19 automated pytest suites and Dockerized multi-port container builds.

