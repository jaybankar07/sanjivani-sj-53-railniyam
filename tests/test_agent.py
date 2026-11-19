"""Tests for RailNiyam agent loop and LangGraph workflow with approval."""
from app.agent_loop import run_agent
from app.graph import run_agent_graph


def test_agent_loop_calculation_vs_policy():
    # Calculation query
    res_calc = run_agent("Cancel confirmed 3AC ticket, fare Rs 1500, cancelled 50 hours before")
    assert res_calc["tool_used"] == "rail_refund_calculator"
    assert res_calc["tool_output"]["refund_amount"] > 0

    # Policy query
    res_policy = run_agent("What is the rule if the railway cancels my train?")
    assert res_policy["tool_used"] == "rag_search"
    assert "answer" in res_policy["tool_output"]


def test_langgraph_approval_workflow():
    thread_id = "test-pytest-thread"

    # Turn 1: Requests approval
    t1 = run_agent_graph("Cancel my 2A ticket, fare Rs 2000, 20 hours before", thread_id=thread_id)
    assert t1["requires_approval"] is True
    assert t1["status"] == "waiting_for_approval"

    # Turn 2: User confirms approval
    t2 = run_agent_graph("confirm", thread_id=thread_id, approve=True)
    assert t2["status"] == "completed"
    assert t2["requires_approval"] is False
    assert t2["details"] is not None
    assert t2["details"]["refund_amount"] > 0

