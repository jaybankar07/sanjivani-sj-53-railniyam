from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.records import load_records, get_by_id
from app.smart_search import SmartSearch

app = FastAPI(title="RailNiyam", description="Indian Railways refund rules Q&A")
RECORDS = load_records()
ENGINE = SmartSearch(RECORDS)
QUESTIONS: list[dict] = []


class Question(BaseModel):
    name: str = "anonymous"
    question: str


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
