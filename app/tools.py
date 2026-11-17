"""RailNiyam agent tools.
Contains rail_refund_calculator: computes exact refund based on 2015 rule table:
- Flat minimum charges per passenger (1A/EC: 240, 2A/FC: 200, 3A/CC/3E: 180, SL: 120, 2S: 60)
- 25% (48h-12h) and 50% (12h-4h) slabs subject to flat minimum
- No refund on confirmed ticket < 4 hours before departure
- No refund on confirmed Tatkal tickets
- Rs 60 clerkage on RAC / Waitlisted cancelled up to 30 mins before departure
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FLAT_MINIMUM_CHARGES = {
    "1A": 240.0,
    "EC": 240.0,
    "2A": 200.0,
    "FC": 200.0,
    "3A": 180.0,
    "CC": 180.0,
    "3E": 180.0,
    "SL": 120.0,
    "2S": 60.0,
}


def normalize_class(travel_class: str) -> str:
    """Normalize user travel class string to standard code."""
    c = travel_class.upper().strip().replace(" ", "").replace("-", "")
    if c in ("1STAC", "FIRSTAC", "1AC", "AC1", "1A"):
        return "1A"
    elif c in ("EXECUTIVE", "EXECUTIVECLASS", "EC"):
        return "EC"
    elif c in ("2NDAC", "SECONDAC", "2AC", "AC2", "2A"):
        return "2A"
    elif c in ("FIRSTCLASS", "FC"):
        return "FC"
    elif c in ("3RDAC", "THIRDAC", "3AC", "AC3", "3A"):
        return "3A"
    elif c in ("CHAIRCAR", "ACCHAIRCAR", "CC"):
        return "CC"
    elif c in ("3AECONOMY", "3ECONOMY", "3E"):
        return "3E"
    elif c in ("SLEEPER", "SLEEPERCLASS", "SL"):
        return "SL"
    elif c in ("SECONDCLASS", "2NDCLASS", "SECOND", "2S"):
        return "2S"
    return "SL"  # Default to Sleeper if unrecognized


def rail_refund_calculator(
    fare: float,
    travel_class: str,
    status: str,
    passengers: int = 1,
    hours_before_departure: float = 49.0,
) -> dict:
    """Compute Indian Railways ticket refund amount and cancellation charge.

    Parameters:
    - fare: Total fare paid (in INR)
    - travel_class: Class (1A, 2A, 3A, CC, SL, 2S, etc.)
    - status: Ticket status ("confirmed", "rac", "wl", "waitlisted", "tatkal")
    - passengers: Number of passengers on ticket (default: 1)
    - hours_before_departure: Hours remaining until scheduled departure

    Returns dict with fare breakdown, deduction, refund amount, and applied rule.
    """
    fare = float(max(0.0, fare))
    passengers = int(max(1, passengers))
    hours = float(hours_before_departure)
    norm_class = normalize_class(travel_class)
    st = status.lower().strip()

    flat_rate = FLAT_MINIMUM_CHARGES.get(norm_class, 120.0)
    total_min_flat = flat_rate * passengers

    # 1. Tatkal Confirmed Ticket
    if "tatkal" in st and ("confirmed" in st or "wl" not in st and "rac" not in st):
        cancellation_charge = fare
        refund_amount = 0.0
        rule_applied = "Tatkal Rule: No refund granted on cancellation of confirmed Tatkal ticket."
        details = (
            f"Under Indian Railways rules w.e.f. 12.11.2015, confirmed Tatkal tickets are non-refundable "
            f"upon voluntary cancellation. Full fare of Rs {fare:.2f} is retained."
        )

    # 2. RAC or Waitlisted (WL) (including Tatkal RAC / WL)
    elif "rac" in st or "wl" in st or "waitlist" in st:
        clerkage_per_passenger = 30.0 if norm_class == "2S" else 60.0
        total_clerkage = clerkage_per_passenger * passengers

        if hours >= 0.5:  # Up to 30 mins before scheduled departure
            cancellation_charge = min(fare, total_clerkage)
            refund_amount = max(0.0, fare - cancellation_charge)
            rule_applied = "Rule 1 & 4 (Levy of Clerkage): Rs 60 clerkage per passenger (Rs 30 for 2S)."
            details = (
                f"RAC/Waitlisted ticket cancelled {hours:.1f} hours before departure (within cutoff of >=0.5h). "
                f"Clerkage charge of Rs {clerkage_per_passenger:.2f} × {passengers} = Rs {cancellation_charge:.2f} "
                f"deducted. Refund: Rs {refund_amount:.2f}."
            )
        else:
            cancellation_charge = fare
            refund_amount = 0.0
            rule_applied = "Rule 4: RAC/WL ticket cancelled less than 30 minutes before departure."
            details = (
                f"RAC/Waitlisted ticket cancelled {hours:.1f} hours before departure (less than 30 minutes). "
                f"No refund is admissible after chart preparation/deadline."
            )

    # 3. Confirmed Ticket (Standard 2015 Slabs)
    else:
        if hours > 48.0:
            cancellation_charge = min(fare, total_min_flat)
            refund_amount = max(0.0, fare - cancellation_charge)
            rule_applied = f"Rule 2(i): Confirmed cancellation >48h before departure (Flat Rs {flat_rate:.2f} per passenger)."
            details = (
                f"Cancelled >48 hours before departure ({hours:.1f}h). Flat charge of Rs {flat_rate:.2f} × {passengers} "
                f"= Rs {cancellation_charge:.2f} deducted. Refund: Rs {refund_amount:.2f}."
            )
        elif 12.0 <= hours <= 48.0:
            pct_deduction = 0.25 * fare
            cancellation_charge = min(fare, max(pct_deduction, total_min_flat))
            refund_amount = max(0.0, fare - cancellation_charge)
            rule_applied = "Rule 2(ii): Confirmed cancellation between 48h and 12h @ 25% (subject to flat min charge)."
            details = (
                f"Cancelled between 48h and 12h before departure ({hours:.1f}h). Deducted 25% of fare (Rs {pct_deduction:.2f}) "
                f"or minimum flat charge (Rs {total_min_flat:.2f}), whichever is higher: Rs {cancellation_charge:.2f}. "
                f"Refund: Rs {refund_amount:.2f}."
            )
        elif 4.0 <= hours < 12.0:
            pct_deduction = 0.50 * fare
            cancellation_charge = min(fare, max(pct_deduction, total_min_flat))
            refund_amount = max(0.0, fare - cancellation_charge)
            rule_applied = "Rule 2(iii): Confirmed cancellation between 12h and 4h @ 50% (subject to flat min charge)."
            details = (
                f"Cancelled between 12h and 4h before departure ({hours:.1f}h). Deducted 50% of fare (Rs {pct_deduction:.2f}) "
                f"or minimum flat charge (Rs {total_min_flat:.2f}), whichever is higher: Rs {cancellation_charge:.2f}. "
                f"Refund: Rs {refund_amount:.2f}."
            )
        else:  # hours < 4.0
            cancellation_charge = fare
            refund_amount = 0.0
            rule_applied = "Rule 2(iv): Confirmed cancellation less than 4 hours before departure."
            details = (
                f"Cancelled less than 4 hours before departure ({hours:.1f}h). Under Indian Railways rules, "
                f"no refund is admissible on confirmed tickets after chart preparation or within 4 hours of departure."
            )

    return {
        "fare": round(fare, 2),
        "passengers": passengers,
        "class": norm_class,
        "status": status,
        "hours_before_departure": hours,
        "flat_minimum_rate": flat_rate,
        "cancellation_charge": round(cancellation_charge, 2),
        "refund_amount": round(refund_amount, 2),
        "rule_applied": rule_applied,
        "details": details,
    }


if __name__ == "__main__":
    # Test cases
    print("--- 1. Confirmed 3AC > 48h (fare Rs 1500, 1 pax) ---")
    print(rail_refund_calculator(1500, "3A", "confirmed", 1, 50.0))

    print("\n--- 2. Confirmed SL 6h before (fare Rs 500, 1 pax) ---")
    print(rail_refund_calculator(500, "SL", "confirmed", 1, 6.0))

    print("\n--- 3. Tatkal Confirmed (fare Rs 2000) ---")
    print(rail_refund_calculator(2000, "3A", "tatkal confirmed", 1, 30.0))

    print("\n--- 4. RAC Ticket (fare Rs 800, 2 pax, 5h before) ---")
    print(rail_refund_calculator(800, "3A", "RAC", 2, 5.0))

