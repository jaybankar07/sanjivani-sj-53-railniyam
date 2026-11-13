from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.records import load_records, get_by_id
from app.smart_search import SmartSearch
from app.llm import chat as llm_chat, parse_llm_json

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


def load_prompt(filename: str, fallback: str = "") -> str:
    path = PROMPTS_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return fallback


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


@app.post("/questions")
def post_question(q: Question):
    top = ENGINE.search(q.question, top_k=3)
    entry = {"id": len(QUESTIONS) + 1, **q.model_dump(),
             "top_matches": [r.id for r, _ in top]}
    QUESTIONS.append(entry)
    return entry


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
    except EnvironmentError:
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

