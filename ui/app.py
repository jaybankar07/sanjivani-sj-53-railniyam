"""RailNiyam Streamlit Application.
Features:
- Streamlit Chat interface connecting to FastAPI /ask and /agent endpoints.
- Displays retrieved citations (Title, Source, Page).
- Thumbs up / thumbs down feedback persisted to data/feedback.json.
- Signature Feature: 'Cancel now or later?' slider with dynamic refund calculations across 48h/12h/4h slabs and official rule citations.
"""
import sys
import json
import time
from pathlib import Path
from datetime import datetime

import streamlit as st
import requests

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.tools import rail_refund_calculator
from app.rag import answer_question
from app.graph import run_agent_graph

FEEDBACK_FILE = ROOT / "data" / "feedback.json"
API_BASE_URL = "http://127.0.0.1:8000"

# --- Page Configuration ---
st.set_page_config(
    page_title="RailNiyam — Railway Refund Assistant",
    page_icon="🚆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS for Styling ---
st.markdown(
    """
    <style>
    .main-title { font-size: 2.2rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.2rem; }
    .sub-title { font-size: 1.05rem; color: #4B5563; margin-bottom: 1.5rem; }
    .slab-card { padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }
    .slab-green { background-color: #ECFDF5; border-left: 5px solid #10B981; }
    .slab-yellow { background-color: #FEFCE8; border-left: 5px solid #F59E0B; }
    .slab-orange { background-color: #FFF7ED; border-left: 5px solid #F97316; }
    .slab-red { background-color: #FEF2F2; border-left: 5px solid #EF4444; }
    .citation-box { background-color: #F3F4F6; padding: 0.6rem 0.9rem; border-radius: 6px; font-size: 0.85rem; margin-top: 0.4rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


def save_feedback(query: str, answer: str, rating: str):
    """Persist user thumbs up / down feedback."""
    feedback_entry = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "answer": answer,
        "rating": rating,
    }
    entries = []
    if FEEDBACK_FILE.exists():
        try:
            entries = json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
        except Exception:
            entries = []
    entries.append(feedback_entry)
    FEEDBACK_FILE.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def call_ask_api(question: str) -> dict:
    """Call /ask endpoint with offline fallback to direct function."""
    try:
        resp = requests.post(f"{API_BASE_URL}/ask", json={"question": question, "top_k": 3}, timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    # Fallback to in-process RAG
    return answer_question(question=question, top_k=3)


def call_agent_api(message: str, thread_id: str, approve: bool | None = None) -> dict:
    """Call /agent endpoint with offline fallback to direct function."""
    try:
        payload = {"message": message, "thread_id": thread_id}
        if approve is not None:
            payload["approve"] = approve
        resp = requests.post(f"{API_BASE_URL}/agent", json=payload, timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    # Fallback to in-process LangGraph
    return run_agent_graph(message=message, thread_id=thread_id, approve=approve)


# --- Header ---
st.markdown("<div class='main-title'>🚆 RailNiyam</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='sub-title'>Your intelligent assistant for Indian Railways ticket refunds, cancellation charges & TDR rules (w.e.f. 12.11.2015).</div>",
    unsafe_allow_html=True,
)

# --- Sidebar: Configuration & Quick Info ---
with st.sidebar:
    st.header("⚙️ Assistant Settings")
    api_mode = st.radio(
        "Select Response Mode:",
        ["/ask (RAG with Citations)", "/agent (LangGraph + Approval)"],
        index=0,
    )
    st.info("💡 **Backend Status**: Connected to FastAPI service (`http://127.0.0.1:8000`).")

    st.markdown("---")
    st.markdown("### 📌 Official 2015 Slabs")
    st.caption("• **> 48 hrs**: Flat minimum deduction per passenger")
    st.caption("• **48h to 12h**: 25% of fare (subject to flat min)")
    st.caption("• **12h to 4h**: 50% of fare (subject to flat min)")
    st.caption("• **< 4 hrs**: No refund on confirmed tickets")
    st.caption("• **RAC / WL**: Rs 60 clerkage up to 30m before departure")
    st.caption("• **Tatkal Confirmed**: Non-refundable")


# --- Main Tabs ---
tab_slider, tab_chat = st.tabs(["⏱️ 'Cancel Now or Later?' Slider (Signature Feature)", "💬 RailNiyam Chat"])


# ==========================================
# TAB 1: 'Cancel now or later?' Slider
# ==========================================
with tab_slider:
    st.subheader("⏱️ 'Cancel now or later?' Live Refund Simulator")
    st.write(
        "Drag the slider to see exactly how your refund and cancellation deduction change across the "
        "**48h / 12h / 4h slabs** under Indian Railways rules."
    )

    col_in1, col_in2, col_in3, col_in4 = st.columns(4)
    with col_in1:
        input_fare = st.number_input("Total Ticket Fare (₹)", min_value=60.0, max_value=50000.0, value=1500.0, step=50.0)
    with col_in2:
        input_class = st.selectbox(
            "Travel Class",
            ["3A (AC 3 Tier)", "SL (Sleeper)", "2A (AC 2 Tier)", "1A (First AC)", "CC (AC Chair Car)", "2S (Second Sitting)", "EC (Exec Chair Car)"],
            index=0,
        )
    with col_in3:
        input_status = st.selectbox("Ticket Status", ["Confirmed", "RAC / Waitlisted", "Tatkal Confirmed"], index=0)
    with col_in4:
        input_passengers = st.number_input("Passengers", min_value=1, max_value=6, value=1, step=1)

    # Class abbreviation
    class_code = input_class.split()[0]

    st.markdown("---")
    st.markdown("#### 🎯 Drag Cancellation Time:")
    hours_slider = st.slider(
        "Hours before scheduled departure of the train:",
        min_value=0.0,
        max_value=72.0,
        value=36.0,
        step=0.5,
        help="Move slider to simulate cancellation timing relative to scheduled departure.",
    )

    # Calculate live refund using tool
    calc_res = rail_refund_calculator(
        fare=input_fare,
        travel_class=class_code,
        status=input_status,
        passengers=input_passengers,
        hours_before_departure=hours_slider,
    )

    # Slab styling & explanation
    slab_class = "slab-green"
    slab_badge = "🟢 Safe Zone (> 48 hours)"
    if input_status == "Tatkal Confirmed":
        slab_class = "slab-red"
        slab_badge = "🔴 Tatkal Non-Refundable"
    elif input_status == "RAC / Waitlisted":
        if hours_slider >= 0.5:
            slab_class = "slab-green"
            slab_badge = "🟢 RAC / WL Clerkage Window (≥ 30 mins)"
        else:
            slab_class = "slab-red"
            slab_badge = "🔴 Chart Prepared (< 30 mins) — No Refund"
    else:
        if hours_slider > 48.0:
            slab_class = "slab-green"
            slab_badge = "🟢 Slab 1: > 48 Hours Before Departure (Flat Min Charge)"
        elif 12.0 <= hours_slider <= 48.0:
            slab_class = "slab-yellow"
            slab_badge = "🟡 Slab 2: 48h to 12h Before Departure (25% Deduction)"
        elif 4.0 <= hours_slider < 12.0:
            slab_class = "slab-orange"
            slab_badge = "🟠 Slab 3: 12h to 4h Before Departure (50% Deduction)"
        else:
            slab_class = "slab-red"
            slab_badge = "🔴 Slab 4: < 4 Hours Before Departure (No Refund Admissible)"

    # Metric Cards
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric(
            label="💵 Net Refund Amount",
            value=f"₹ {calc_res['refund_amount']:.2f}",
            delta=f"You receive {round((calc_res['refund_amount']/input_fare)*100)}% of fare" if input_fare > 0 else "0%",
        )
    with col_m2:
        st.metric(
            label="✂️ Cancellation Deduction",
            value=f"₹ {calc_res['cancellation_charge']:.2f}",
            delta=f"- ₹ {calc_res['cancellation_charge']:.2f}",
            delta_color="inverse",
        )
    with col_m3:
        st.metric(label="⏱️ Simulation Time", value=f"{hours_slider:.1f} hrs before train")

    # Dynamic Slab Card
    st.markdown(
        f"""
        <div class='slab-card {slab_class}'>
            <h4 style='margin:0 0 0.3rem 0;'>{slab_badge}</h4>
            <p style='margin:0; font-size: 0.95rem;'>{calc_res['details']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Official Rule Citation
    st.markdown(
        f"""
        <div class='citation-box'>
            <b>📜 Official Rule Citation:</b> <code>{calc_res['rule_applied']}</code><br/>
            <i>Authority: South Central Railway (SCR) Gazette Notification w.e.f. 12.11.2015 & IRCTC Master Refund Circular.</i>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Comparative Slab Timeline Table
    st.markdown("#### 📊 Comparative Timeline: 'Cancel Now vs Later'")
    sim_times = [60.0, 30.0, 8.0, 2.0]
    sim_rows = []
    for t in sim_times:
        r = rail_refund_calculator(input_fare, class_code, input_status, input_passengers, t)
        sim_rows.append({
            "Time Window": "> 48 Hours" if t > 48 else ("48h to 12h" if t >= 12 else ("12h to 4h" if t >= 4 else "< 4 Hours")),
            "Simulated Timing": f"{t:.0f} hrs before departure",
            "Deduction (₹)": f"₹ {r['cancellation_charge']:.2f}",
            "Refund (₹)": f"₹ {r['refund_amount']:.2f}",
            "Rule Reference": r["rule_applied"].split(":")[0],
        })
    st.table(sim_rows)


# ==========================================
# TAB 2: Streamlit Chat
# ==========================================
with tab_chat:
    st.subheader("💬 Ask RailNiyam")
    st.caption("Ask questions in natural language. Powered by grounded RAG, citations, and LangGraph agent memory.")

    # Initialize chat history & thread ID
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! I am RailNiyam. Ask me any question about Indian Railways refund rules, cancellation charges, TDR deadlines, or ticket scenarios.",
                "citations": [],
            }
        ]
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = f"st-{int(time.time())}"

    # Display chat messages
    for idx, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            # Display citations if present
            if msg.get("citations"):
                st.markdown("**Citations:**")
                for c in msg["citations"]:
                    st.markdown(
                        f"""
                        <div class='citation-box'>
                            <b>📌 {c.get('title', 'Rule')}</b><br/>
                            <span style='color: #4B5563;'>Source: {c.get('source', '')} | Page {c.get('page', 1)} | Similarity: {c.get('score', 0.0):.2f}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            # Thumbs Up / Down feedback for assistant responses (skip initial greeting)
            if msg["role"] == "assistant" and idx > 0:
                col_fb1, col_fb2, col_fb3 = st.columns([0.05, 0.05, 0.9])
                with col_fb1:
                    if st.button("👍", key=f"thumb_up_{idx}", help="Helpful answer"):
                        save_feedback(
                            query=st.session_state.messages[idx - 1]["content"] if idx > 0 else "",
                            answer=msg["content"],
                            rating="up",
                        )
                        st.toast("Feedback saved: Helpful! 👍")
                with col_fb2:
                    if st.button("👎", key=f"thumb_down_{idx}", help="Not helpful / incorrect"):
                        save_feedback(
                            query=st.session_state.messages[idx - 1]["content"] if idx > 0 else "",
                            answer=msg["content"],
                            rating="down",
                        )
                        st.toast("Feedback saved: Flagged for review 👎")

    # Chat input
    if prompt := st.chat_input("Ask about refund rules, cancellation fee, or calculate ticket refund..."):
        # Append user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate Assistant Response
        with st.chat_message("assistant"):
            with st.spinner("Searching RailNiyam rules database..."):
                citations = []
                if "/agent" in api_mode:
                    agent_res = call_agent_api(message=prompt, thread_id=st.session_state.thread_id)
                    reply_text = agent_res.get("response", "No response generated.")
                    if agent_res.get("requires_approval"):
                        st.warning("⚠️ Action requires your confirmation. Reply with 'Yes' to confirm.")
                else:
                    rag_res = call_ask_api(question=prompt)
                    reply_text = rag_res.get("answer", "No answer found.")
                    citations = rag_res.get("citations", [])

                st.markdown(reply_text)

                if citations:
                    st.markdown("**Citations:**")
                    for c in citations:
                        st.markdown(
                            f"""
                            <div class='citation-box'>
                                <b>📌 {c.get('title', 'Rule')}</b><br/>
                                <span style='color: #4B5563;'>Source: {c.get('source', '')} | Page {c.get('page', 1)} | Similarity: {c.get('score', 0.0):.2f}</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

            # Append assistant message to session state
            st.session_state.messages.append({
                "role": "assistant",
                "content": reply_text,
                "citations": citations,
            })
