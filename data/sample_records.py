"""18 hand-made records: 10 refund rules (SCR table) + 8 TDR reasons.
verified=False means not confirmed against the official page/PDF."""
RULES = "https://www.indianrail.gov.in/refund_Rules.html"
TDR1 = "https://pnrstatuslive.com/cancellation-refund-tdr-policy-of-indian-railways"
TDR2 = "https://news.visitinrajasthan.com/?p=11536"
REF = "SCR Refund Rules w.e.f. 12.11.2015"

def r(i, cat, topic, status, window, charge, ref, url, ok=True):
    return dict(id=i, category=cat, rule_topic=topic, ticket_status=status,
                time_window=window, charge_or_refund=charge, rule_ref=ref,
                source_url=url, verified=ok)

RECORDS = [
    r(1, "cancellation", "Confirmed ticket cancelled early", "Confirmed", "More than 48 hours before departure",
      "Flat per passenger: Rs 240 (1A/EC), 200 (2A/FC), 180 (3A/CC/3E), 120 (SL), 60 (2S)", f"{REF}, Rule 2(i)", RULES),
    r(2, "cancellation", "Confirmed ticket, 48 to 12 hours", "Confirmed", "Between 48 and 12 hours before departure",
      "25% of fare, subject to the minimum flat charge in row 1", f"{REF}, Rule 2(ii)", RULES),
    r(3, "cancellation", "Confirmed ticket, 12 to 4 hours", "Confirmed", "Between 12 and 4 hours before departure",
      "50% of fare, subject to the minimum flat charge in row 1", f"{REF}, Rule 2(iii)", RULES),
    r(4, "cancellation", "Confirmed ticket, last 4 hours", "Confirmed", "Less than 4 hours before departure",
      "No refund after the prescribed time limit", f"{REF}, Rule 2(iv)", RULES),
    r(5, "cancellation", "Partially confirmed ticket", "Partially confirmed", "Up to half an hour before scheduled departure",
      "Refund allowed (earlier limit was 2 hours after departure)", f"{REF}, Rule 3", RULES),
    r(6, "clerkage", "RAC / waitlisted ticket cancelled", "RAC / WL", "Up to half an hour before scheduled departure",
      "Clerkage Rs 60 per passenger deducted (second class reserved and other classes); no refund after limit", f"{REF}, Rules 1 and 4", RULES),
    r(7, "eticket", "Train cancelled, e-ticket", "E-ticket", "When railway cancels the train",
      "Automatic refund w.e.f. 01.07.2015; no TDR needed. Counter PRS tickets unchanged", f"{REF}, Rule 5", RULES),
    r(8, "tatkal", "Confirmed Tatkal ticket cancelled", "Tatkal confirmed", "Any time (voluntary cancellation)",
      "No refund on voluntary cancellation", "Tatkal rule (secondary source)", "https://irctconline.pages.dev/guides/refund-rules", False),
    r(9, "tatkal", "Tatkal RAC / waitlisted ticket", "Tatkal RAC / WL", "Up to half an hour before scheduled departure",
      "Refund with clerkage deduction (verify exact Tatkal handling)", "Tatkal rule (verify in circular PDF)", RULES, False),
    r(10, "clerkage", "Unreserved ticket cancelled", "Unreserved", "Time limit not stated on the one-page table",
      "Clerkage Rs 30 per passenger (second class unreserved)", f"{REF}, Rule 1(i)", RULES),

    r(11, "tdr", "Train cancelled by railways", "Any reserved", "No time limit for e-tickets",
      "Full refund; automatic for e-tickets", "IRCTC TDR table", TDR1),
    r(12, "tdr", "Train late more than 3 hours", "Passenger did not travel", "TDR before actual departure at boarding station",
      "Full fare refunded, no cancellation charge or clerkage", "IRCTC TDR table; SCR rule 6", TDR2),
    r(13, "tdr", "AC failure", "AC class passenger", "Within 20 hours of arrival at destination",
      "Fare difference for distance AC failed; original TTE certificate needed", "IRCTC TDR table", TDR2),
    r(14, "tdr", "Proper coach not attached", "Booked class not available", "Up to 2 days from TTE certificate",
      "Difference of fare to lower class travelled", "IRCTC TDR table", TDR2),
    r(15, "tdr", "Travelled in lower class after charting", "No room provided after charting", "Within 3 hours of actual departure",
      "Difference of fare as passenger travelled in lower class", "IRCTC TDR table", TDR1, False),
    r(16, "tdr", "Train diverted, route skips station", "Boarding or destination not touched", "See IRCTC TDR table",
      "Refund when train does not touch boarding or destination station", "IRCTC TDR table", TDR1, False),
    r(17, "tdr", "Reservation given in lower class", "Passenger did not travel", "Within 3 hours of actual departure",
      "Refund as passenger declined the lower class", "IRCTC TDR table", TDR2),
    r(18, "tdr", "Party partially travelled", "Part of party travelled", "Up to 72 hours from scheduled departure",
      "Refund on unused part of ticket", "IRCTC TDR table", TDR2),
]

if __name__ == "__main__":
    import sys
    recs = RECORDS
    print(f"All {len(recs)} records:")
    for x in recs:
        print(f"[{x['id']:>2}] {x['category']:<12} {x['rule_topic']} | {x['time_window']} -> {x['charge_or_refund']}")
    kw = (sys.argv[1] if len(sys.argv) > 1 else "tatkal").lower()
    hits = [x for x in recs if kw in " ".join(map(str, x.values())).lower()]
    print(f"\nSearch '{kw}': {len(hits)} hit(s)")
    for x in hits:
        print(" -", x["rule_topic"])
    counts = {}
    for x in recs:
        counts[x["category"]] = counts.get(x["category"], 0) + 1
    print("\nCount per category:", counts)
