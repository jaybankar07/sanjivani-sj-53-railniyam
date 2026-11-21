import logging
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel, Field

from app.cache import QUERY_CACHE, estimate_tokens
from app.graph import run_agent_graph
from app.llm import chat as llm_chat
from app.llm import parse_llm_json
from app.rag import answer_question
from app.records import get_by_id, load_records
from app.smart_search import SmartSearch
from app.vectorstore import search_semantic

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("railniyam")


ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "prompts"

app = FastAPI(title="RailNiyam", description="Indian Railways refund rules Q&A")
RECORDS = load_records()
ENGINE = SmartSearch(RECORDS)
QUESTIONS: list[dict] = []


class Question(BaseModel):
    name: str = "anonymous"
    question: str


class ChatRequest(BaseModel):
    question: str
    prompt_version: str = "v1"


class ChatResponse(BaseModel):
    answer: str
    confidence: str
    follow_up: str


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500, description="Passenger question (max 500 characters)")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of context chunks to retrieve")


class AskResponse(BaseModel):
    question: str
    answer: str
    citations: list[dict]
    confidence: str
    latency_ms: float | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    cached: bool = False


class AgentRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="User request to agent")
    thread_id: str = Field(default="default", max_length=100)
    approve: bool | None = None


class AgentResponse(BaseModel):
    thread_id: str
    response: str
    status: str
    action_taken: str | None = None
    requires_approval: bool = False
    details: dict | None = None
    latency_ms: float | None = None
    tokens: int | None = None



def load_prompt(filename: str, fallback: str = "") -> str:
    path = PROMPTS_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return fallback


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


@app.get("/health")
def health():
    return {"status": "ok", "records": len(RECORDS)}


@app.get("/records")
def list_records(limit: int = 10):
    return [r.to_dict() for r in RECORDS[:max(limit, 0)]]


@app.get("/records/{record_id}")
def one_record(record_id: int):
    rec = get_by_id(RECORDS, record_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return rec.to_dict()


@app.get("/search")
def search(q: str):
    return [{"score": round(s, 3), **r.to_dict()} for r, s in ENGINE.search(q)]


@app.get("/search/semantic")
def search_semantic_endpoint(q: str, limit: int = 5):
    return search_semantic(query=q, top_k=limit)


@app.post("/questions")
def post_question(q: Question):
    top = ENGINE.search(q.question, top_k=3)
    entry = {"id": len(QUESTIONS) + 1, **q.model_dump(),
             "top_matches": [r.id for r, _ in top]}
    QUESTIONS.append(entry)
    return entry


@app.get("/cache/stats")
def cache_stats():
    """Return in-memory cache statistics (hits, misses, hit rate)."""
    return QUERY_CACHE.stats()


@app.delete("/cache")
def clear_cache():
    """Clear query cache."""
    QUERY_CACHE.clear()
    return {"status": "cleared"}


@app.post("/ask", response_model=AskResponse)
def ask_endpoint(req: AskRequest):
    # Enforce input limit guard
    if len(req.question.strip()) > 500:
        raise HTTPException(status_code=400, detail="Question exceeds maximum allowed limit of 500 characters")

    t0 = time.time()

    # Check cache
    cached_data = QUERY_CACHE.get(req.question)
    if cached_data is not None:
        latency_ms = round((time.time() - t0) * 1000, 2)
        logger.info(
            f"[TELEMETRY] POST /ask | latency={latency_ms:.2f}ms | "
            f"prompt_tokens={cached_data['prompt_tokens']} | completion_tokens={cached_data['completion_tokens']} | "
            f"total_tokens={cached_data['total_tokens']} | cached=True"
        )
        return AskResponse(
            question=req.question,
            answer=cached_data["answer"],
            citations=cached_data["citations"],
            confidence=cached_data["confidence"],
            latency_ms=latency_ms,
            prompt_tokens=cached_data["prompt_tokens"],
            completion_tokens=cached_data["completion_tokens"],
            total_tokens=cached_data["total_tokens"],
            cached=True,
        )

    # Compute answer via RAG
    result = answer_question(question=req.question, top_k=req.top_k)
    latency_ms = round((time.time() - t0) * 1000, 2)

    prompt_tok = estimate_tokens(req.question)
    compl_tok = estimate_tokens(result["answer"])
    tot_tok = prompt_tok + compl_tok

    # Populate cache
    QUERY_CACHE.set(req.question, {
        "answer": result["answer"],
        "citations": result["citations"],
        "confidence": result["confidence"],
        "prompt_tokens": prompt_tok,
        "completion_tokens": compl_tok,
        "total_tokens": tot_tok,
    })

    logger.info(
        f"[TELEMETRY] POST /ask | latency={latency_ms:.2f}ms | "
        f"prompt_tokens={prompt_tok} | completion_tokens={compl_tok} | "
        f"total_tokens={tot_tok} | cached=False"
    )

    return AskResponse(
        question=result["question"],
        answer=result["answer"],
        citations=result["citations"],
        confidence=result["confidence"],
        latency_ms=latency_ms,
        prompt_tokens=prompt_tok,
        completion_tokens=compl_tok,
        total_tokens=tot_tok,
        cached=False,
    )


@app.post("/agent", response_model=AgentResponse)
def agent_endpoint(req: AgentRequest):
    if len(req.message.strip()) > 1000:
        raise HTTPException(status_code=400, detail="Message exceeds maximum allowed limit of 1000 characters")

    t0 = time.time()
    result = run_agent_graph(
        message=req.message,
        thread_id=req.thread_id,
        approve=req.approve,
    )
    latency_ms = round((time.time() - t0) * 1000, 2)
    tot_tok = estimate_tokens(req.message) + estimate_tokens(result.get("response", ""))

    logger.info(
        f"[TELEMETRY] POST /agent | thread_id={req.thread_id} | latency={latency_ms:.2f}ms | "
        f"total_tokens={tot_tok} | action={result.get('action_taken')}"
    )

    return AgentResponse(
        **result,
        latency_ms=latency_ms,
        tokens=tot_tok,
    )



@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    system_prompt = load_prompt("system.txt", "You are RailNiyam assistant for Indian Railways refund rules.")
    task_file = f"task_{req.prompt_version}.txt" if req.prompt_version in ("v1", "v2") else "task_v1.txt"
    task_template = load_prompt(task_file, "Question: {question}\nContext: {context}")

    top_matches = ENGINE.search(req.question, top_k=3)
    if top_matches:
        context_str = "\n".join(
            f"- [{r.id}] {r.rule_topic} (Ticket: {r.ticket_status}, Window: {r.time_window}): "
            f"{r.charge_or_refund} (Ref: {r.rule_ref})"
            for r, s in top_matches
        )
    else:
        context_str = "No directly matching refund rules found in database."

    user_prompt = task_template.format(question=req.question, context=context_str)

    try:
        raw_reply = llm_chat([{"role": "user", "content": user_prompt}], system=system_prompt)
        parsed = parse_llm_json(raw_reply)
        return ChatResponse(**parsed)
    except OSError:
        # Graceful fallback when API keys are not yet configured in .env
        if top_matches:
            top_rec, _ = top_matches[0]
            answer = f"According to rule [{top_rec.rule_topic}]: {top_rec.charge_or_refund} (Window: {top_rec.time_window})."
            confidence = "medium"
            follow_up = "Would you like to know the rules for a different ticket status or class?"
        else:
            answer = "The RailNiyam database cannot answer this question as no matching refund rule was found."
            confidence = "low"
            follow_up = "Could you specify ticket status (Confirmed, RAC, WL, or Tatkal)?"
        return ChatResponse(answer=answer, confidence=confidence, follow_up=follow_up)

