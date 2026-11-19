"""Tests for record loading, counting, and ID retrieval."""
from app.records import count_by, get_by_id, load_records


def test_load_records_structure():
    records = load_records()
    assert len(records) >= 18
    first = records[0]
    assert hasattr(first, "rule_topic")
    assert hasattr(first, "ticket_status")
    assert hasattr(first, "time_window")
    assert hasattr(first, "charge_or_refund")
    assert hasattr(first, "rule_ref")
    assert hasattr(first, "source_url")


def test_get_by_id():
    records = load_records()
    rec1 = get_by_id(records, 1)
    assert rec1 is not None
    assert rec1.id == 1
    assert "confirmed" in rec1.rule_topic.lower()

    rec_missing = get_by_id(records, 9999)
    assert rec_missing is None


def test_count_by_category():
    records = load_records()
    counts = count_by(records, "category")
    assert isinstance(counts, dict)
    assert "cancellation" in counts
    assert "tdr" in counts
    assert sum(counts.values()) == len(records)

