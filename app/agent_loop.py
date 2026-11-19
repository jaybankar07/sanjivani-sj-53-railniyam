"""Hand-written Agent Loop for RailNiyam.
Orchestrates between:
1. RAG Search (app.rag.answer_question) for policy and rule questions.
2. Rail Refund Calculator (app.tools.rail_refund_calculator) for exact numerical refund calculations.
Provides step-by-step reasoning trace, tool execution, and synthesized response.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.rag import answer_question
from app.tools import rail_refund_calculator


def extract_calculation_params(query: str) -> dict | None:
    """Extract fare, class, status, hours, and passengers from query text using heuristics."""
    q = query.lower()

    # Detect fare: e.g. "rs 1200", "rs. 1200", "1500 rs", "fare of 800", "fare 500"
    fare_match = re.search(r"(?:rs\.?|inr|fare\s*(?:of|is|:)?)\s*(\d+(?:\.\d+)?)", q)
    if not fare_match:
        fare_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:rs|rupees|inr)", q)

    fare = float(fare_match.group(1)) if fare_match else None

    # Detect class
    class_match = re.search(r"\b(1a|2a|3a|3ac|2ac|1ac|cc|ec|fc|sl|2s|1st\s*ac|2nd\s*ac|3rd\s*ac|sleeper|chair\s*car)\b", q)
    travel_class = class_match.group(1) if class_match else "SL"

    # Detect status
    status = "confirmed"
    if "tatkal" in q:
        status = "tatkal confirmed" if "wl" not in q and "rac" not in q else "tatkal rac"
    elif "rac" in q:
        status = "RAC"
    elif "wl" in q or "waitlist" in q:
        status = "WL"

    # Detect hours / days before departure
    hours = 50.0  # default >48h
    days_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:day|days)", q)
    hours_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:hour|hours|hr|hrs)", q)
    mins_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:minute|minutes|min|mins)", q)

    if days_match:
        hours = float(days_match.group(1)) * 24.0
    elif hours_match:
        hours = float(hours_match.group(1))
    elif mins_match:
        hours = float(mins_match.group(1)) / 60.0

    # Detect passengers
    pax_match = re.search(r"(\d+)\s*(?:passenger|passengers|person|people|pax|ticket|tickets)", q)
    passengers = int(pax_match.group(1)) if pax_match else 1

    # Check if calculation was explicitly requested or fare is present
    has_calc_intent = any(w in q for w in ["calculate", "deduct", "how much will i get", "refund amount", "exact refund"])
    if fare is not None or (has_calc_intent and ("hour" in q or "day" in q or "class" in q)):
        return {
            "fare": fare if fare is not None else 1000.0,
            "travel_class": travel_class,
            "status": status,
            "passengers": passengers,
            "hours_before_departure": hours,
            "extracted_fare": fare is not None,
        }
    return None


class RailNiyamAgent:
    """Hand-written agent with reasoning, tool selection, and trace execution."""

    def __init__(self):
        self.name = "RailNiyamAgent"

    def run(self, user_query: str) -> dict:
        trace = []
        trace.append({"step": "receive_input", "query": user_query})

        # 1. Evaluate intent
        calc_params = extract_calculation_params(user_query)

        # 2. Decision logic
        if calc_params is not None and calc_params["extracted_fare"]:
            # Route to Rail Refund Calculator tool
            trace.append({
                "step": "decide_tool",
                "tool": "rail_refund_calculator",
                "reason": "Numerical refund calculation requested with explicit ticket parameters.",
                "parameters": calc_params,
            })

            calc_res = rail_refund_calculator(
                fare=calc_params["fare"],
                travel_class=calc_params["travel_class"],
                status=calc_params["status"],
                passengers=calc_params["passengers"],
                hours_before_departure=calc_params["hours_before_departure"],
            )
            trace.append({"step": "tool_execution", "tool": "rail_refund_calculator", "output": calc_res})

            response = (
                f"### Refund Calculation Result:\n"
                f"- **Total Fare**: Rs {calc_res['fare']:.2f} ({calc_res['passengers']} passenger(s), Class: {calc_res['class']}, Status: {calc_res['status']})\n"
                f"- **Time Before Departure**: {calc_res['hours_before_departure']:.1f} hours\n"
                f"- **Cancellation Charge Deducted**: **Rs {calc_res['cancellation_charge']:.2f}**\n"
                f"- **Net Refund Amount**: **Rs {calc_res['refund_amount']:.2f}**\n\n"
                f"**Rule Applied**: {calc_res['rule_applied']}\n\n"
                f"*{calc_res['details']}*"
            )

            return {
                "query": user_query,
                "tool_used": "rail_refund_calculator",
                "tool_output": calc_res,
                "response": response,
                "trace": trace,
            }

        else:
            # Route to RAG Search tool
            trace.append({
                "step": "decide_tool",
                "tool": "rag_search",
                "reason": "Policy or informational refund query requiring document retrieval and citations.",
            })

            rag_res = answer_question(user_query, top_k=3)
            trace.append({"step": "tool_execution", "tool": "rag_search", "output": rag_res})

            response = rag_res["answer"]
            return {
                "query": user_query,
                "tool_used": "rag_search",
                "tool_output": rag_res,
                "response": response,
                "trace": trace,
            }


_AGENT = RailNiyamAgent()


def run_agent(query: str) -> dict:
    """Run the hand-written RailNiyam agent on a user query."""
    return _AGENT.run(query)


if __name__ == "__main__":
    print("=== TEST 1: Calculation Query ===")
    res1 = run_agent("Calculate refund for confirmed 3AC ticket, fare Rs 1600, cancelled 5 hours before departure.")
    print(res1["response"])
    print("\nTrace:", [t["step"] for t in res1["trace"]])

    print("\n=== TEST 2: Policy Query ===")
    res2 = run_agent("What is the rule if train is cancelled by railways?")
    print(res2["response"])
    print("\nTrace:", [t["step"] for t in res2["trace"]])
