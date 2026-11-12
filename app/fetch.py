"""Download source documents into data/raw/ with timeouts and error handling."""
from pathlib import Path
import requests

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
SOURCES = {
    "refund_rules.html": "https://www.indianrail.gov.in/refund_Rules.html",
    "RefundRules.pdf": "https://refunds.indianrail.gov.in/ref_rules/REFUND_RULES_CIRCULARS/RefundRules.pdf",
}
HEADERS = {"User-Agent": "RailNiyam-student-project/0.1"}


def fetch_all() -> dict:
    RAW.mkdir(parents=True, exist_ok=True)
    results = {}
    for name, url in SOURCES.items():
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            (RAW / name).write_bytes(resp.content)
            results[name] = f"ok ({len(resp.content)} bytes)"
        except requests.RequestException as e:
            results[name] = f"FAILED: {e}"
    return results


if __name__ == "__main__":
    for k, v in fetch_all().items():
        print(f"{k}: {v}")
