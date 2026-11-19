"""Tests for keyword search, TF-IDF smart search, and Chroma semantic search."""
from app.records import load_records, search
from app.smart_search import SmartSearch
from app.vectorstore import search_semantic


def test_keyword_search():
    records = load_records()
    tatkal_hits = search(records, "tatkal")
    assert len(tatkal_hits) >= 2
    for r in tatkal_hits:
        assert "tatkal" in r.text().lower()


def test_smart_search_tfidf():
    records = load_records()
    engine = SmartSearch(records)
    results = engine.search("cancelled train e-ticket refund", top_k=3)
    assert len(results) > 0
    top_record, score = results[0]
    assert score > 0.0
    assert hasattr(top_record, "rule_topic")


def test_semantic_search_chroma():
    hits = search_semantic("How much deducted if confirmed ticket cancelled 2 days early?", top_k=3)
    assert len(hits) > 0
    first = hits[0]
    assert "chunk_id" in first
    assert "title" in first
    assert "source" in first
    assert "page" in first
    assert "score" in first
    assert first["score"] >= 0.0

