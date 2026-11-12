import json
from pathlib import Path
from collections import Counter
from app.models import Record

ROOT = Path(__file__).resolve().parent.parent
JSON_PATH = ROOT / "data" / "records.json"


def load_records() -> list[Record]:
    """Load data/records.json (from ingest); fall back to the 18 sample records."""
    if JSON_PATH.exists():
        data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    else:
        from data.sample_records import RECORDS as data
    return [Record.from_dict(d) for d in data]


def search(records: list[Record], keyword: str) -> list[Record]:
    kw = keyword.lower()
    return [r for r in records if kw in " ".join(map(str, r.to_dict().values())).lower()]


def count_by(records: list[Record], field: str = "category") -> dict:
    return dict(Counter(getattr(r, field) for r in records))


def get_by_id(records: list[Record], record_id: int) -> Record | None:
    return next((r for r in records if r.id == record_id), None)
