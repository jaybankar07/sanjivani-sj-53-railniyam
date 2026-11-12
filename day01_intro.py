product = "RailNiyam"
user = "Train passenger who needs to cancel a ticket"
problem = "Refund rules are scattered across tables, PDFs and TDR pages"
data_source = "Indian Railways Refund Rules w.e.f. 12.11.2015 + IRCTC TDR table"

print("=" * 50)
print(f"PROJECT CARD: {product}")
print(f"User    : {user}")
print(f"Problem : {problem}")
print(f"Data    : {data_source}")
print("=" * 50)

name = input("Your name: ").strip()
question = input("Your question about train refunds: ").strip()
print(f"\nHello {name}! You asked: '{question}'")
print(f"{product} will answer this from {data_source}.")
