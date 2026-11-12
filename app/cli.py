from app.records import load_records, search, count_by


def main():
    records = load_records()
    while True:
        print("\n1 print all | 2 search | 3 count per category | 0 exit")
        c = input("> ").strip()
        if c == "1":
            for r in records:
                print(f"[{r.id:>2}] {r.category:<12} {r.rule_topic} -> {r.charge_or_refund}")
        elif c == "2":
            hits = search(records, input("keyword: "))
            print(f"{len(hits)} hit(s)")
            for r in hits:
                print(f" - [{r.id}] {r.rule_topic}")
        elif c == "3":
            print(count_by(records))
        elif c == "0":
            break


if __name__ == "__main__":
    main()
