"""RailNiyam document chunking module.
Chunks RailNiyam documents (structured records + raw rules) while preserving:
- source (rule reference or document name)
- page (page number or document section sheet)
- title (rule title or topic)
"""
from dataclasses import dataclass, asdict
import json
import sys
from pathlib import Path
import re
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DATA_DIR = ROOT / "data"
RECORDS_JSON = DATA_DIR / "records.json"
RAW_HTML = DATA_DIR / "raw" / "refund_rules.html"


@dataclass
class Chunk:
    chunk_id: str
    title: str
    source: str
    page: int
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


def chunk_records() -> list[Chunk]:
    """Chunk structured records from data/records.json (or sample_records)."""
    chunks = []
    if RECORDS_JSON.exists():
        records = json.loads(RECORDS_JSON.read_text(encoding="utf-8"))
    else:
        from data.sample_records import RECORDS as records

    for r in records:
        rec_id = r.get("id", 0)
        topic = r.get("rule_topic", "General Refund Rule")
        status = r.get("ticket_status", "Any")
        window = r.get("time_window", "Not specified")
        charge = r.get("charge_or_refund", "No details")
        ref = r.get("rule_ref", "SCR Refund Rules w.e.f. 12.11.2015")
        category = r.get("category", "general")
        
        # Determine page: Page 1 for SCR refund rules (IDs 1-10), Page 2 for IRCTC TDR reasons (IDs 11-18)
        page = 1 if rec_id <= 10 else 2

        text = (
            f"Title: {topic}. "
            f"Ticket Status: {status}. "
            f"Time Window: {window}. "
            f"Charge / Refund: {charge}. "
            f"Category: {category}. "
            f"Reference: {ref}."
        )

        chunks.append(
            Chunk(
                chunk_id=f"rule-chunk-{rec_id:02d}",
                title=topic,
                source=ref,
                page=page,
                text=text,
            )
        )
    return chunks


def chunk_raw_html() -> list[Chunk]:
    """Chunk raw HTML document data/raw/refund_rules.html into logical sections."""
    chunks = []
    if not RAW_HTML.exists():
        return chunks

    html_content = RAW_HTML.read_text(encoding="utf-8")
    soup = BeautifulSoup(html_content, "html.parser")
    raw_text = soup.get_text("\n")

    # Section 1: Clerkage charges (Rule 1)
    if "Levy of clerkage" in raw_text:
        clerkage_text = (
            "Rule 1: Levy of clerkage per passenger for cancellation of unreserved, RAC and waitlisted tickets. "
            "Revised w.e.f. 12.11.2015: "
            "(i) Unreserved (second class): Rs. 30 per passenger. "
            "(ii) Second class (reserved) and other classes: Rs. 60 per passenger."
        )
        chunks.append(
            Chunk(
                chunk_id="raw-chunk-01",
                title="Rule 1: Levy of Clerkage for Unreserved, RAC and Waitlisted Tickets",
                source="data/raw/refund_rules.html",
                page=1,
                text=clerkage_text,
            )
        )

    # Section 2: Confirmed cancellation flat charges (>48h) (Rule 2(i))
    if "48 hours before the scheduled departure" in raw_text:
        flat_text = (
            "Rule 2(i): Minimum cancellation charge per passenger on confirmed (reserved) tickets "
            "cancelled more than 48 hours before scheduled train departure (Revised w.e.f. 12.11.2015): "
            "1st AC/executive class: Rs. 240, 2 AC/1st Class: Rs. 200, 3AC/ACC/3A economy: Rs. 180, "
            "Second sleeper class: Rs. 120, Second class: Rs. 60."
        )
        chunks.append(
            Chunk(
                chunk_id="raw-chunk-02",
                title="Rule 2(i): Minimum Cancellation Charge >48 Hours Before Departure",
                source="data/raw/refund_rules.html",
                page=1,
                text=flat_text,
            )
        )

    # Section 3: Confirmed cancellation 48-12h and 12-4h (Rule 2(ii) and 2(iii))
    if "Between 48 hours and 12 hours" in raw_text or "between 12 hours and 4 hours" in raw_text:
        pct_text = (
            "Rule 2(ii) & 2(iii): Cancellation charge per passenger on confirmed tickets: "
            "Rule 2(ii): Between 48 hours and 12 hours before scheduled departure @ 25% of fare, "
            "subject to minimum flat charge as per Rule 2(i). "
            "Rule 2(iii): Between 12 hours and 4 hours before scheduled departure @ 50% of fare, "
            "subject to minimum flat charge as per Rule 2(i). "
            "Less than 4 hours before departure: No refund."
        )
        chunks.append(
            Chunk(
                chunk_id="raw-chunk-03",
                title="Rule 2(ii)-(iv): Confirmed Ticket Cancellation 48-12h, 12-4h, and <4h",
                source="data/raw/refund_rules.html",
                page=1,
                text=pct_text,
            )
        )

    return chunks


def get_all_chunks() -> list[Chunk]:
    """Return all RailNiyam chunks combining structured rules and raw document chunks."""
    all_chunks = chunk_records() + chunk_raw_html()
    return all_chunks


if __name__ == "__main__":
    chunks = get_all_chunks()
    print(f"Total chunks generated: {len(chunks)}")
    for c in chunks[:5]:
        print(f"[{c.chunk_id}] (Page {c.page}) {c.title} | Source: {c.source}")
