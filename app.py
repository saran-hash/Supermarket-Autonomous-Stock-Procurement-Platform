"""Streamlit Frontend for Supermarket Autonomous Stock & Procurement Platform."""

import glob
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

import storelib
from agent.agentic_harness import AgenticSupermarketHarness
from agent.agent import SupermarketAgentOrchestrator
from agent.llm_client import get_api_key, get_model

# Page Configuration
st.set_page_config(
    page_title="Supermarket Autonomous Procurement",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for polished supermarket dashboard look
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        border-left: 5px solid #28a745;
        margin-bottom: 12px;
    }
    .stAlert {
        border-radius: 8px;
    }
    .po-box {
        background-color: #f1f8e9;
        border: 1px solid #c8e6c9;
        border-radius: 8px;
        padding: 12px;
        font-family: monospace;
        white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Settings
st.sidebar.image("https://img.icons8.com/fluency/96/supermarket.png", width=70)
st.sidebar.title("Procurement AI")
st.sidebar.caption("Autonomous Stock & Vendor Dispatch")

api_key = get_api_key()
active_model = get_model()

if api_key:
    st.sidebar.success(f"🟢 LLM Active: `{active_model}`")
else:
    st.sidebar.warning("🟡 Simulation Mode (No OpenRouter Key)")

st.sidebar.markdown("---")
eval_date = st.sidebar.date_input("Simulation Date", datetime.strptime("2026-10-25", "%Y-%m-%d"))
eval_date_str = eval_date.strftime("%Y-%m-%d")

spending_limit = st.sidebar.number_input("Max Auto-Order Cap (₹)", value=50000.0, step=5000.0)
auto_approve = st.sidebar.checkbox("Auto-Approve Over-Limit POs", value=False)

st.sidebar.markdown("---")
st.sidebar.caption("Supermarket Agent Ecosystem • Built with OpenRouter & Streamlit")

# Main Page Header
col_header, col_action = st.columns([3, 1])
with col_header:
    st.title("🛒 Supermarket Autonomous Replenishment")
    st.caption("Tri-Agent Ecosystem: Festival Scout → Stock Monitor → Procurement Dispatcher")

with col_action:
    if st.button("🚀 Run Full Cycle", type="primary", use_container_width=True):
        with st.spinner("Executing autonomous 3-agent pipeline..."):
            orch = SupermarketAgentOrchestrator()
            orch.run_full_lifecycle(eval_date=eval_date_str, dry_run=True, auto_approve=auto_approve)
        st.success("Replenishment cycle completed!")
        st.rerun()

# Tabs
tab_chat, tab_inventory, tab_dealers, tab_orders = st.tabs([
    "💬 AI Store Copilot",
    "📦 Inventory & Shortages",
    "🤝 Supplier Optimization",
    "📋 Dispatched POs & WhatsApp",
])

# -----------------------------------------------------------------------------
# TAB 1: AI Store Copilot
# -----------------------------------------------------------------------------
with tab_chat:
    st.subheader("Autonomous Store Assistant")
    st.caption("Ask questions, audit stock, or instruct the AI to negotiate & reorder.")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello Store Director! I am your Autonomous Procurement Copilot. Ask me about stock levels, upcoming festivals, or tell me to run replenishment."}
        ]
    if "harness" not in st.session_state:
        st.session_state.harness = AgenticSupermarketHarness()

    # Quick prompt buttons
    qcol1, qcol2, qcol3, qcol4 = st.columns(4)
    if qcol1.button("Check Diwali festival impact"):
        user_prompt = "Check upcoming Diwali festival impact on our stock."
    elif qcol2.button("Audit all deficit items"):
        user_prompt = "Audit inventory and tell me which products are below threshold."
    elif qcol3.button("Compare Sugar quotes"):
        user_prompt = "Inspect dealer quotes for Sugar and tell me who has the best price."
    elif qcol4.button("Restock Edible Oils"):
        user_prompt = "Check stock for Sunflower Oil and prepare purchase orders if low."
    else:
        user_prompt = None

    # Display chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Handle Input
    chat_input = st.chat_input("Ask or command your procurement agent...") or user_prompt
    if chat_input:
        st.session_state.messages.append({"role": "user", "content": chat_input})
        with st.chat_message("user"):
            st.markdown(chat_input)

        with st.chat_message("assistant"):
            with st.spinner("Agent is reasoning and invoking skills..."):
                resp = st.session_state.harness.run_goal(chat_input, verbose=False)
                st.markdown(resp)
        st.session_state.messages.append({"role": "assistant", "content": resp})

# -----------------------------------------------------------------------------
# TAB 2: Live Inventory Monitor
# -----------------------------------------------------------------------------
with tab_inventory:
    st.subheader("Warehouse & Shelf Stock Status")
    stock_path = storelib.data_path("inventory", "daily_stock.csv")
    req_path = storelib.data_path("inventory", "reorder_requisitions.json")

    if stock_path.exists():
        df_stock = pd.read_csv(stock_path)

        # Merge with requisitions if available
        flagged_skus = set()
        if req_path.exists():
            try:
                with open(req_path, "r", encoding="utf-8") as f:
                    reqs = json.load(f)
                    flagged_skus = {r["sku_id"] for r in reqs}
            except Exception:
                pass

        df_stock["Status"] = df_stock["sku_id"].apply(
            lambda s: "🚨 REORDER NEEDED" if s in flagged_skus else "🟢 HEALTHY"
        )

        # Summary KPIs
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Total Tracked SKUs", len(df_stock))
        kpi2.metric("Critical Deficits", len(flagged_skus))
        kpi3.metric("Staples Items", len(df_stock[df_stock["category"] == "Staples"]))
        kpi4.metric("Active Multiplier", "2.2x (Diwali)" if "2026-10" in eval_date_str else "1.0x")

        # Category filter
        cat = st.selectbox("Filter Category", ["All"] + sorted(df_stock["category"].unique().tolist()))
        if cat != "All":
            df_stock = df_stock[df_stock["category"] == cat]

        st.dataframe(
            df_stock[["sku_id", "product_name", "category", "current_stock", "base_unit", "reorder_point", "Status"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No stock data found.")

# -----------------------------------------------------------------------------
# TAB 3: Procurement & Supplier Optimization
# -----------------------------------------------------------------------------
with tab_dealers:
    st.subheader("Wholesale Supplier Directory & Optimization")
    dealer_master = storelib.data_path("dealers", "dealer_master.csv")
    plan_path = storelib.data_path("orders", "procurement_plan.json")

    if dealer_master.exists():
        st.markdown("##### Registered Suppliers")
        df_dealers = pd.read_csv(dealer_master)
        st.dataframe(df_dealers, use_container_width=True, hide_index=True)

    if plan_path.exists():
        st.markdown("##### Current Procurement Plan (Optimized)")
        with open(plan_path, "r", encoding="utf-8") as f:
            plan = json.load(f)

        for d_id, data in plan.items():
            val = data.get("total_order_value", 0.0)
            exceeds = val > spending_limit
            card_color = "⚠️" if exceeds else "✅"

            with st.expander(f"{card_color} {data['dealer_name']} ({d_id}) — Total: ₹{val:,.2f} via {data['preferred_channel'].upper()}", expanded=True):
                if exceeds:
                    st.warning(f"🚨 **High-Value Spending Alert:** This order exceeds the ₹{spending_limit:,.2f} auto-dispatch limit by ₹{(val - spending_limit):,.2f}.")
                st.write(f"**Contact:** Phone: `{data.get('phone_whatsapp')}` | Email: `{data.get('email')}`")
                st.table(pd.DataFrame(data.get("items", [])))

# -----------------------------------------------------------------------------
# TAB 4: Dispatched POs & WhatsApp Messages
# -----------------------------------------------------------------------------
with tab_orders:
    st.subheader("Purchase Order Audit Trail & AI-Crafted WhatsApp Messages")
    po_log_path = storelib.data_path("orders", "po_log.csv")

    col_audit, col_msg = st.columns([1, 1])

    with col_audit:
        st.markdown("##### Historical PO Log")
        if po_log_path.exists():
            df_po = pd.read_csv(po_log_path)
            st.dataframe(df_po.tail(20), use_container_width=True, hide_index=True)
        else:
            st.info("No POs logged yet.")

    with col_msg:
        st.markdown("##### AI-Generated WhatsApp / Email PO Messages")
        notif_dir = storelib.data_path("orders", "notifications")
        files = list(notif_dir.glob("*.txt")) if notif_dir.exists() else []

        if files:
            selected_file = st.selectbox("Inspect Notification Artifact", [f.name for f in reversed(files)])
            if selected_file:
                content = (notif_dir / selected_file).read_text(encoding="utf-8")
                st.text_area("Message Preview", content, height=350)
        else:
            st.info("Run a replenishment cycle to see AI-generated messages.")
