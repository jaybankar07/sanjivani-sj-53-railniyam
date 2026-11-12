# RailNiyam

**Product:** RailNiyam, a Q&A assistant for Indian Railways ticket refund and cancellation rules.
**User:** An ordinary train passenger (e.g. a student or family traveller) who wants to know what they get back when they cancel a ticket or when the railway fails them.
**Problem:** Refund rules are split across a one-page table, circular PDFs and the IRCTC TDR table. People guess, lose money, or miss TDR deadlines.
**Data source:** Indian Railways refund rules w.e.f. 12.11.2015 (https://www.indianrail.gov.in/refund_Rules.html), the Refund Rules circular PDF (refunds.indianrail.gov.in) and the IRCTC TDR reasons table.

**6 questions this project answers:**
1. How much is deducted if I cancel a confirmed 3AC ticket 3 days before departure?
2. If I cancel a confirmed Sleeper ticket 6 hours before departure, how much do I get back?
3. My train was cancelled by railways — do I need to file a TDR for my e-ticket?
4. Is there any refund if I cancel a confirmed Tatkal ticket?
5. My train is running more than 3 hours late and I don't want to travel — what can I claim?
6. *(Data cannot answer)* What exact amount will IRCTC credit to my bank, and in how many days?

## How to run
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python day01_intro.py              # project card + name/question
python day01_menu.py               # menu
python -m app.cli                  # records CLI (print / search / count)
python -m app.fetch                # download raw docs into data/raw/
python -m app.ingest               # clean raw -> data/records.json
python analysis/explore.py         # 3 pandas facts
uvicorn app.main:app --reload      # API; open http://127.0.0.1:8000/docs
```

## Endpoints
`GET /health`, `GET /records?limit=`, `GET /records/{id}` (404 if missing), `GET /search?q=` (TF-IDF + cosine), `POST /questions`.

## Data caveat
Records with `"verified": false` come from secondary sources or memory and must be checked against the official table/PDF.
