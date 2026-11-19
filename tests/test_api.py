"""Tests for FastAPI endpoints: /health, /records, and /ask with a fake LLM."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["records"] >= 18


def test_records_endpoint():
    resp = client.get("/records?limit=5")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 5

    resp_single = client.get("/records/1")
    assert resp_single.status_code == 200
    assert resp_single.json()["id"] == 1

    resp_404 = client.get("/records/9999")
    assert resp_404.status_code == 404


def test_ask_with_fake_llm(monkeypatch):
    """Test /ask endpoint by monkeypatching llm_chat with a fake LLM function."""
    def fake_llm_chat(messages: list[dict], system: str) -> str:
        return (
            "According to official Indian Railways rules, full refund is automatically credited "
            "for e-tickets when train is cancelled [Source: SCR Refund Rules w.e.f. 12.11.2015, Rule 5, Page 1]."
        )

    # Monkeypatch the LLM in app.rag module
    import app.rag
    monkeypatch.setattr(app.rag, "llm_chat", fake_llm_chat)

    resp = client.post("/ask", json={"question": "My train was cancelled. Do I get refund for e-ticket?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "automatically credited" in data["answer"]
    assert len(data["citations"]) > 0
    assert data["citations"][0]["chunk_id"] is not None


def test_ask_q6_unanswerable():
    """Verify that Q6 or unanswerable queries explicitly return 'I don't know'."""
    q6 = "What is the exact amount IRCTC will credit to my bank account today, and in how many days will it arrive?"
    resp = client.post("/ask", json={"question": q6})
    assert resp.status_code == 200
    data = resp.json()
    assert "i don't know" in data["answer"].lower()
    assert len(data["citations"]) == 0
    assert data["confidence"] == "low"

