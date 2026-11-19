"""LangGraph implementation of the RailNiyam Agent.
Features:
- StateGraph workflow with state persistence via MemorySaver.
- Dual tool integration: RAG search (app.rag) and Rail Refund Calculator (app.tools).
- Human-in-the-loop approval step for ticket refund/cancellation confirmation.
"""
import sys
from pathlib import Path
from typing import TypedDict

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.agent_loop import extract_calculation_params
from app.rag import answer_question
from app.tools import rail_refund_calculator


class AgentState(TypedDict, total=False):
    user_input: str
    thread_id: str
    intent: str
    calc_params: dict | None
    tool_result: dict | None
    requires_approval: bool
    approved: bool | None
    response: str
    status: str
    history: list[dict]


# --- Graph Nodes ---

def router_node(state: AgentState) -> dict:
    """Analyze the user input and determine whether to calculate, ask approval, or RAG."""
    msg = state.get("user_input", "").strip()
    calc_params = extract_calculation_params(msg)

    # Check if previously waiting for approval and receiving an approval flag or keyword
    was_waiting = state.get("status") == "waiting_for_approval"
    approved_flag = state.get("approved")

    # If already waiting for approval
    if was_waiting:
        if approved_flag is True or any(w in msg.lower() for w in ["yes", "approve", "confirm", "proceed"]):
            return {
                "intent": "execute_approved",
                "approved": True,
                "requires_approval": False,
            }
        elif approved_flag is False or any(w in msg.lower() for w in ["no", "cancel", "stop", "abort"]):
            return {
                "intent": "rejection",
                "approved": False,
                "requires_approval": False,
            }

    # If numerical calculation parameters are present
    if calc_params is not None and calc_params.get("extracted_fare"):
        # Explicit approval required before confirming ticket cancellation/refund
        if approved_flag is True:
            return {
                "intent": "calculate",
                "calc_params": calc_params,
                "requires_approval": False,
                "approved": True,
            }
        else:
            return {
                "intent": "need_approval",
                "calc_params": calc_params,
                "requires_approval": True,
            }

    # Default to informational RAG query
    return {
        "intent": "rag",
        "requires_approval": False,
    }


def rag_node(state: AgentState) -> dict:
    """Execute RAG retrieval and answer synthesis with citations."""
    query = state.get("user_input", "")
    rag_result = answer_question(query, top_k=3)
    return {
        "tool_result": rag_result,
        "response": rag_result.get("answer", ""),
        "status": "completed",
    }


def approval_node(state: AgentState) -> dict:
    """Pause and request user approval before executing refund/cancellation."""
    params = state.get("calc_params", {})
    fare = params.get("fare", 0.0)
    travel_class = params.get("travel_class", "SL")
    status = params.get("status", "confirmed")
    hours = params.get("hours_before_departure", 48.0)

    prompt = (
        f"⚠️ **Approval Required for Refund Confirmation**\n\n"
        f"You are requesting refund processing for a **{status.upper()}** ticket ({travel_class}) "
        f"with total fare of **Rs {fare:.2f}** ({hours:.1f} hours before departure).\n\n"
        f"Under Indian Railways 2015 rules, cancellation charges will be deducted from your fare.\n"
        f"**Do you approve proceeding with this refund calculation and cancellation?**\n"
        f"(Set `approve: true` in your request or reply 'Yes' to confirm)."
    )
    return {
        "response": prompt,
        "status": "waiting_for_approval",
        "requires_approval": True,
    }


def calculate_node(state: AgentState) -> dict:
    """Execute refund calculation tool."""
    params = state.get("calc_params") or extract_calculation_params(state.get("user_input", "")) or {}
    fare = params.get("fare", 1000.0)
    travel_class = params.get("travel_class", "SL")
    status = params.get("status", "confirmed")
    passengers = params.get("passengers", 1)
    hours = params.get("hours_before_departure", 50.0)

    result = rail_refund_calculator(
        fare=fare,
        travel_class=travel_class,
        status=status,
        passengers=passengers,
        hours_before_departure=hours,
    )

    response = (
        f"✅ **Refund Calculation Verified & Approved:**\n\n"
        f"- **Ticket Details**: {result['passengers']} Passenger(s) | Class {result['class']} | Status: {result['status']}\n"
        f"- **Time Before Departure**: {result['hours_before_departure']:.1f} hours\n"
        f"- **Original Fare**: Rs {result['fare']:.2f}\n"
        f"- **Cancellation Deduction**: **Rs {result['cancellation_charge']:.2f}**\n"
        f"- **Refund Amount Creditable**: **Rs {result['refund_amount']:.2f}**\n\n"
        f"**Official Rule**: {result['rule_applied']}\n\n"
        f"*{result['details']}*"
    )
    return {
        "tool_result": result,
        "response": response,
        "status": "completed",
        "requires_approval": False,
    }


def rejection_node(state: AgentState) -> dict:
    """Handle user rejection or cancellation of action."""
    return {
        "response": "❌ Action cancelled by user. No refund calculation or cancellation was processed.",
        "status": "rejected",
        "requires_approval": False,
        "approved": False,
    }


# --- Conditional Routing ---

def route_next_step(state: AgentState) -> str:
    intent = state.get("intent", "rag")
    if intent == "need_approval":
        return "approval_node"
    elif intent == "calculate" or intent == "execute_approved":
        return "calculate_node"
    elif intent == "rejection":
        return "rejection_node"
    return "rag_node"


# --- Workflow Graph Builder ---

def build_agent_graph():
    builder = StateGraph(AgentState)

    builder.add_node("router", router_node)
    builder.add_node("rag_node", rag_node)
    builder.add_node("approval_node", approval_node)
    builder.add_node("calculate_node", calculate_node)
    builder.add_node("rejection_node", rejection_node)

    builder.set_entry_point("router")

    builder.add_conditional_edges(
        "router",
        route_next_step,
        {
            "approval_node": "approval_node",
            "calculate_node": "calculate_node",
            "rag_node": "rag_node",
            "rejection_node": "rejection_node",
        },
    )

    builder.add_edge("rag_node", END)
    builder.add_edge("approval_node", END)
    builder.add_edge("calculate_node", END)
    builder.add_edge("rejection_node", END)

    memory = MemorySaver()
    return builder.compile(checkpointer=memory)


AGENT_GRAPH = build_agent_graph()


def run_agent_graph(message: str, thread_id: str = "default", approve: bool | None = None) -> dict:
    """Execute a turn through the LangGraph agent with memory and approval check."""
    config = {"configurable": {"thread_id": thread_id}}

    inputs: AgentState = {
        "user_input": message,
        "thread_id": thread_id,
    }
    if approve is not None:
        inputs["approved"] = approve

    final_state = AGENT_GRAPH.invoke(inputs, config=config)

    return {
        "thread_id": thread_id,
        "response": final_state.get("response", ""),
        "status": final_state.get("status", "completed"),
        "action_taken": final_state.get("intent"),
        "requires_approval": final_state.get("requires_approval", False),
        "details": final_state.get("tool_result"),
    }


if __name__ == "__main__":
    t_id = "test-thread-01"

    print("=== TURN 1: Calculation requesting approval ===")
    t1 = run_agent_graph("I want to cancel my confirmed 3AC ticket, fare Rs 1800, 20 hours before departure.", thread_id=t_id)
    print("Status:", t1["status"])
    print("Requires approval:", t1["requires_approval"])
    print("Response:\n", t1["response"])

    print("\n=== TURN 2: User Approves ===")
    t2 = run_agent_graph("Yes, proceed with cancellation", thread_id=t_id, approve=True)
    print("Status:", t2["status"])
    print("Response:\n", t2["response"])

    print("\n=== TURN 3: Informational RAG Query ===")
    t3 = run_agent_graph("Do I need a TDR for e-ticket if train is cancelled?", thread_id="test-thread-02")
    print("Status:", t3["status"])
    print("Response:\n", t3["response"])

