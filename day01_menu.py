SAMPLES = [
    "How much is deducted if I cancel a confirmed 3AC ticket 2 days early?",
    "Do I get a refund if my train is 4 hours late?",
    "Is a confirmed Tatkal ticket refundable?",
]

while True:
    print("\n--- RailNiyam ---")
    print("1. About RailNiyam")
    print("2. Sample questions")
    print("3. Refund rule check")
    print("0. Exit")
    choice = input("Choose: ").strip()

    if choice == "1":
        print("RailNiyam answers Indian Railways refund/cancellation questions.")
    elif choice == "2":
        for i, q in enumerate(SAMPLES, 1):
            print(f"{i}. {q}")
    elif choice == "3":
        try:
            hours = float(input("Hours before departure (confirmed ticket): "))
        except ValueError:
            print("Please enter a number.")
            continue
        if hours > 48:
            print("Flat cancellation charge applies (Rs 60 to Rs 240 by class).")
        elif hours > 12:
            print("25% of fare, subject to the minimum flat charge.")
        elif hours > 4:
            print("50% of fare, subject to the minimum flat charge.")
        else:
            print("No refund on a confirmed ticket after this limit.")
    elif choice == "0":
        print("Goodbye!")
        break
    else:
        print("Invalid choice.")
