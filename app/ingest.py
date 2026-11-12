"""Clean data/raw/refund_rules.html into records and save data/records.json."""
import json
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from data.sample_records import RECORDS as CURATED  # TDR rows (separate IRCTC table)

RAW = ROOT / "data" / "raw" / "refund_rules.html"
OUT = ROOT / "data" / "records.json"
URL = "https://www.indianrail.gov.in/refund_Rules.html"
REF = "SCR Refund Rules w.e.f. 12.11.2015"


def read_text() -> str:
    return re.sub(r"[ \t]+", " ", BeautifulSoup(RAW.read_text(encoding="utf-8"), "html.parser").get_text("\n"))


def parse(text: str) -> dict:
    revised = text.split("Cancellation charge per passenger on confirmed")[-1]
    clerk = text.split("Levy of clerkage")[-1]
    names = {"1A/EC": r"1st AC/executive class", "2A/FC": r"2 ?AC/1st Class",
             "3A/CC/3E": r"3AC/ACC/3A economy", "SL": r"Second sleeper class", "2S": r"Second class\s*:"}
    flat = {}
    for key, pat in names.items():
        m = re.search(pat + r"[^R\n]*Rs\.?\s*(\d+)", revised)
        flat[key] = int(m.group(1)) if m else None
    pct = [int(x) for x in re.findall(r"@\s*(\d+)%", revised)]
    unres = re.search(r"Unreserved \(second class\):\s*Rs\.?\s*(\d+)", clerk)
    other = re.search(r"other classes:\s*Rs\.?\s*(\d+)", clerk)
    return {"flat": flat, "pct": pct,
            "unres": int(unres.group(1)) if unres else None,
            "other": int(other.group(1)) if other else None}


def build(p: dict) -> list[dict]:
    rows = []
    for rec in CURATED[:10]:
        try:
            rec = dict(rec)
            if rec["id"] == 1:
                f = p["flat"]
                if None in f.values():
                    raise ValueError(f"missing flat charge: {f}")
                rec["charge_or_refund"] = "Flat per passenger: " + ", ".join(f"Rs {v} ({k})" for k, v in f.items())
            elif rec["id"] == 2:
                rec["charge_or_refund"] = f"{p['pct'][0]}% of fare, subject to the minimum flat charge"
            elif rec["id"] == 3:
                rec["charge_or_refund"] = f"{p['pct'][1]}% of fare, subject to the minimum flat charge"
            elif rec["id"] == 6:
                rec["charge_or_refund"] = f"Clerkage Rs {p['other']} per passenger deducted; no refund after limit"
            elif rec["id"] == 10:
                rec["charge_or_refund"] = f"Clerkage Rs {p['unres']} per passenger (second class unreserved)"
            rec["source_url"] = rec["source_url"] or URL
            rows.append(rec)
        except (ValueError, IndexError, TypeError) as e:
            print(f"skipping row {rec.get('id')}: {e}")
    return rows


def main():
    try:
        parsed = parse(read_text())
    except FileNotFoundError:
        sys.exit("data/raw/refund_rules.html missing. Run: python -m app.fetch")
    rows = build(parsed) + [dict(r) for r in CURATED[10:]]
    OUT.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(rows)} records to {OUT}  (parsed: {parsed})")


if __name__ == "__main__":
    main()
