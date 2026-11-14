# Semantic Search Evaluation (`eval/search_results.md`)

This report records the semantic search results for the 10 real RailNiyam questions across chunks indexed in the persistent Chroma collection (`railniyam_chunks`).

Each chunk preserves metadata:
- **`title`**: Rule topic or section name
- **`source`**: Official circular reference or file path
- **`page`**: Page number (Page 1 = SCR Refund Rules circular, Page 2 = IRCTC TDR Table)

---

## 1. Semantic Search Results across 10 User Questions

### Question 1: How much will be deducted if I cancel a confirmed 3AC ticket 3 days before departure?
- **Top Hit 1**: `[rule-chunk-01]` Confirmed ticket cancelled early (>48h)
  - **Source**: `SCR Refund Rules w.e.f. 12.11.2015, Rule 2(i)` | **Page**: 1 | **Score**: 0.4405
- **Top Hit 2**: `[rule-chunk-06]` RAC / waitlisted ticket cancelled
  - **Source**: `SCR Refund Rules w.e.f. 12.11.2015, Rules 1 and 4` | **Page**: 1 | **Score**: 0.3839
- **Top Hit 3**: `[rule-chunk-05]` Partially confirmed ticket
  - **Source**: `SCR Refund Rules w.e.f. 12.11.2015, Rule 3` | **Page**: 1 | **Score**: 0.3486
- **Evaluation**: **Hit (Relevant)**. Rule 2(i) explicitly provides the flat deduction for 3AC (Rs 180 per passenger) when cancelled >48 hours before departure.

---

### Question 2: If I cancel a confirmed Sleeper ticket 6 hours before departure, how much do I get back?
- **Top Hit 1**: `[rule-chunk-04]` Confirmed ticket, last 4 hours
  - **Source**: `SCR Refund Rules w.e.f. 12.11.2015, Rule 2(iv)` | **Page**: 1 | **Score**: 0.6890
- **Top Hit 2**: `[rule-chunk-03]` Confirmed ticket, 12 to 4 hours
  - **Source**: `SCR Refund Rules w.e.f. 12.11.2015, Rule 2(iii)` | **Page**: 1 | **Score**: 0.4438
- **Top Hit 3**: `[rule-chunk-05]` Partially confirmed ticket
  - **Source**: `SCR Refund Rules w.e.f. 12.11.2015, Rule 3` | **Page**: 1 | **Score**: 0.3825
- **Evaluation**: **Hit (Relevant)**. Top hits retrieve the 12 to 4 hour window (50% deduction of fare subject to minimum flat charge) alongside the adjacent cutoff boundaries.

---

### Question 3: My train was cancelled by the railways. Do I need to file a TDR for my e-ticket?
- **Top Hit 1**: `[rule-chunk-11]` Train cancelled by railways
  - **Source**: `IRCTC TDR table` | **Page**: 2 | **Score**: 0.7481
- **Top Hit 2**: `[rule-chunk-07]` Train cancelled, e-ticket
  - **Source**: `SCR Refund Rules w.e.f. 12.11.2015, Rule 5` | **Page**: 1 | **Score**: 0.3267
- **Top Hit 3**: `[rule-chunk-16]` Train diverted, route skips station
  - **Source**: `IRCTC TDR table` | **Page**: 2 | **Score**: 0.2168
- **Evaluation**: **Hit (Direct Match)**. `rule-chunk-11` and `rule-chunk-07` answer directly that full refund is automatic for e-tickets and no TDR is required.

---

### Question 4: Is there any refund if I cancel a confirmed Tatkal ticket?
- **Top Hit 1**: `[rule-chunk-08]` Confirmed Tatkal ticket cancelled
  - **Source**: `Tatkal rule (secondary source)` | **Page**: 1 | **Score**: 0.7810
- **Top Hit 2**: `[rule-chunk-09]` Tatkal RAC / waitlisted ticket
  - **Source**: `Tatkal rule (verify in circular PDF)` | **Page**: 1 | **Score**: 0.4473
- **Top Hit 3**: `[rule-chunk-04]` Confirmed ticket, last 4 hours
  - **Source**: `SCR Refund Rules w.e.f. 12.11.2015, Rule 2(iv)` | **Page**: 1 | **Score**: 0.2201
- **Evaluation**: **Hit (Direct Match)**. `rule-chunk-08` directly answers: zero refund granted on voluntary cancellation of a confirmed Tatkal ticket.

---

### Question 5: My train is running more than 3 hours late and I do not want to travel. What can I claim?
- **Top Hit 1**: `[rule-chunk-12]` Train late more than 3 hours
  - **Source**: `IRCTC TDR table; SCR rule 6` | **Page**: 2 | **Score**: 0.5048
- **Top Hit 2**: `[rule-chunk-17]` Reservation given in lower class
  - **Source**: `IRCTC TDR table` | **Page**: 2 | **Score**: 0.2352
- **Top Hit 3**: `[rule-chunk-07]` Train cancelled, e-ticket
  - **Source**: `SCR Refund Rules w.e.f. 12.11.2015, Rule 5` | **Page**: 1 | **Score**: 0.1612
- **Evaluation**: **Hit (Direct Match)**. `rule-chunk-12` specifies full fare refund with no clerkage or cancellation deduction if TDR filed before departure.

---

### Question 6: *(Data cannot answer)* What is the exact amount IRCTC will credit to my bank account today, and in how many days will it arrive?
- **Top Hit 1**: `[rule-chunk-14]` Proper coach not attached
  - **Source**: `IRCTC TDR table` | **Page**: 2 | **Score**: 0.2925
- **Top Hit 2**: `[rule-chunk-09]` Tatkal RAC / waitlisted ticket
  - **Source**: `Tatkal rule (verify in circular PDF)` | **Page**: 1 | **Score**: 0.2358
- **Top Hit 3**: `[rule-chunk-16]` Train diverted, route skips station
  - **Source**: `IRCTC TDR table` | **Page**: 2 | **Score**: 0.1940
- **Evaluation**: **Correctly Unmatched (No Relevant Rule)**. All semantic scores are very low; no rule in the database covers dynamic banking timelines or daily transaction processing.

---

### Question 7: What is the clerkage charge for an RAC or waitlisted ticket?
- **Top Hit 1**: `[rule-chunk-06]` RAC / waitlisted ticket cancelled
  - **Source**: `SCR Refund Rules w.e.f. 12.11.2015, Rules 1 and 4` | **Page**: 1 | **Score**: 0.5056
- **Top Hit 2**: `[rule-chunk-09]` Tatkal RAC / waitlisted ticket
  - **Source**: `Tatkal rule (verify in circular PDF)` | **Page**: 1 | **Score**: 0.3550
- **Top Hit 3**: `[raw-chunk-01]` Rule 1: Levy of Clerkage for Unreserved, RAC and Waitlisted Tickets
  - **Source**: `data/raw/refund_rules.html` | **Page**: 1 | **Score**: 0.2316
- **Evaluation**: **Hit (Direct Match)**. `rule-chunk-06` and `raw-chunk-01` both confirm Rs 60 clerkage charge per passenger up to 30 minutes before departure.

---

### Question 8: The AC did not work in my 3AC coach. Can I get a refund and what proof do I need?
- **Top Hit 1**: `[rule-chunk-13]` AC failure
  - **Source**: `IRCTC TDR table` | **Page**: 2 | **Score**: 0.5685
- **Top Hit 2**: `[raw-chunk-02]` Rule 2(i): Minimum Cancellation Charge >48 Hours Before Departure
  - **Source**: `data/raw/refund_rules.html` | **Page**: 1 | **Score**: 0.4582
- **Top Hit 3**: `[rule-chunk-14]` Proper coach not attached
  - **Source**: `IRCTC TDR table` | **Page**: 2 | **Score**: 0.3944
- **Evaluation**: **Hit (Direct Match)**. `rule-chunk-13` explicitly specifies fare difference refund and that original TTE certificate is required within 20 hours of arrival.

---

### Question 9: I travelled in a lower class because my coach was not attached. How do I claim the fare difference?
- **Top Hit 1**: `[rule-chunk-15]` Travelled in lower class after charting
  - **Source**: `IRCTC TDR table` | **Page**: 2 | **Score**: 0.7912
- **Top Hit 2**: `[rule-chunk-14]` Proper coach not attached
  - **Source**: `IRCTC TDR table` | **Page**: 2 | **Score**: 0.7635
- **Top Hit 3**: `[rule-chunk-17]` Reservation given in lower class
  - **Source**: `IRCTC TDR table` | **Page**: 2 | **Score**: 0.3879
- **Evaluation**: **Hit (Direct Match)**. Both `rule-chunk-15` and `rule-chunk-14` directly cover coach non-attachment and lower-class travel fare difference claims.

---

### Question 10: Until how long before departure can I cancel a partially confirmed ticket?
- **Top Hit 1**: `[rule-chunk-05]` Partially confirmed ticket
  - **Source**: `SCR Refund Rules w.e.f. 12.11.2015, Rule 3` | **Page**: 1 | **Score**: 0.6247
- **Top Hit 2**: `[rule-chunk-04]` Confirmed ticket, last 4 hours
  - **Source**: `SCR Refund Rules w.e.f. 12.11.2015, Rule 2(iv)` | **Page**: 1 | **Score**: 0.2332
- **Top Hit 3**: `[rule-chunk-03]` Confirmed ticket, 12 to 4 hours
  - **Source**: `SCR Refund Rules w.e.f. 12.11.2015, Rule 2(iii)` | **Page**: 1 | **Score**: 0.2100
- **Evaluation**: **Hit (Direct Match)**. `rule-chunk-05` confirms refund is allowed up to 30 minutes before scheduled departure.

---

## 2. Summary Metrics

| Metric | Result |
|---|:---:|
| **Total Chunks in Collection** | 21 chunks |
| **Questions Evaluated** | 10 questions |
| **Relevant Top-3 Retrieval Rate** | **9 / 9 (100% of answerable questions)** |
| **Unanswerable Detection (Q6)** | **1 / 1 (No false-positive high score)** |
| **Metadata Retention (Source, Page, Title)** | **100% across all hits** |

