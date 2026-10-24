# Supermarket Autonomous Stock & Procurement Platform

An autonomous multi-agent platform for supermarket inventory monitoring, seasonal demand forecasting, and automated purchase order dispatch.

Built with a deterministic analysis engine and an agentic orchestration harness, it links inventory data, dealer catalogues, and seasonal calendars to prevent stock-outs, optimize procurement costs, and dispatch Purchase Orders (POs) automatically via WhatsApp Cloud API and Email.

---

## 🏗️ Architecture & Core Philosophy

Like modern industrial data platforms, this repository enforces a strict separation between **deterministic computation** and **conversational / agentic reasoning**:

1. **Deterministic Skills (Zero Calculation Hallucinations):**
   - All inventory deficits, reorder points (ROPs), vendor scoring formulas, and total costs are computed using parameterised Python scripts (`storelib.py`, Pandas).
   - The LLM never invents numbers, sums purchase orders, or guesses prices.

2. **Tri-Agent Ecosystem:**
   - **Agent 1: Festival & Seasonal Demand Scout:** Scans upcoming holidays and local market events to dynamically adjust category safety stock.
   - **Agent 2: Inventory & Stock Maintenance Monitor:** Continuously audits stock levels against baseline and festival-adjusted reorder thresholds.
   - **Agent 3: Procurement & Vendor Dispatcher:** Evaluates live dealer price lists, MOQs, lead times, and ratings, selects the optimal supplier, formats formal POs, and sends them via WhatsApp or Email.

3. **Code vs. Data Separation:**
   - Code is version-controlled in this repository.
   - Transactional data (POS feeds, live stock, dealer price lists, generated POs) resides in an isolated data store referenced via `STORE_DATA_ROOT`.

---

## 📁 Repository Structure

```text
├── AGENTS.md                   # Canonical operating rules, normalization standards, and agent contracts
├── storelib.py                 # Central normalization engine (SKUs, quantities, units, dealers)
├── catalog/
│   └── DATA_CATALOG.md         # Semantic data catalog (schemas, joins, and grain definitions)
├── data/                       # Default local data store (inventory, dealers, calendar, orders)
│   ├── inventory/
│   │   └── daily_stock.csv
│   ├── dealers/
│   │   ├── dealer_master.csv
│   │   └── price_lists/
│   ├── calendar/
│   │   └── festivals.csv
│   └── orders/
│       └── po_log.csv
├── skills/
│   ├── festival-demand/        # Calculates dynamic safety stock multipliers
│   ├── stock-monitor/          # Audits inventory and generates reorder requisitions
│   ├── procurement-optimizer/  # Evaluates dealers and selects optimal vendor
│   └── po-dispatch/            # Generates PDF PO and dispatches via WhatsApp / Email
├── agent/
│   ├── agent.py                # Multi-agent orchestrator with approval gate
│   ├── context.py              # Context & system prompt builder
│   ├── llm_client.py           # OpenRouter API client with .env loading
│   ├── smart_notifier.py       # AI-crafted WhatsApp POs & Manager Approval Briefs
│   ├── guardrails.py           # Spending gates, safety bounds, and read-only sandboxing
│   └── channels/               # Communication adapters (WhatsApp, Email)
├── tests/                      # Automated test suite (skills, storelib, notifier)
└── run_pipeline.py             # End-to-end simulation runner
```

---

## ⚡ Quick Start

### 1. Installation & Environment Setup
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Set your OpenRouter API key in `.env`:
```ini
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxx
OPENROUTER_MODEL=google/gemini-2.0-flash-001  # or meta-llama/llama-3.3-70b-instruct
```

### 2. Run Deterministic Skills Directly
You can run any skill as a standalone script:

```bash
# 1. Check upcoming festivals and calculate surge multipliers
python skills/festival-demand/forecast_demand.py --date 2026-10-25

# 2. Audit current inventory levels
python skills/stock-monitor/audit_stock.py

# 3. Optimize procurement for deficit items
python skills/procurement-optimizer/select_dealer.py

# 4. Generate & dispatch Purchase Orders (dry-run mode)
python skills/po-dispatch/dispatch_po.py --dry-run
```

### 3. Run Full Simulation Pipeline
```bash
# Run simulation cycle
python run_pipeline.py

# Run with interactive Store Manager approval prompts for high-value orders
python run_pipeline.py --interactive

# Run with automated policy override approval
python run_pipeline.py --auto-approve
```

### 4. Launch Streamlit Web Dashboard
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) to interact with:
- 💬 **AI Store Copilot Chat:** Conversational autonomous inventory assistant.
- 📦 **Live Inventory Monitor:** Visual inventory tables with deficit badges and ROP thresholds.
- 🤝 **Supplier Optimization:** Vendor catalogs, pricing comparisons, and spending warnings.
- 📋 **Orders & WhatsApp:** Purchase Order history and formatted WhatsApp dispatch message preview.


---

## 🛡️ Guardrails & AI Smart Approval Flow
- **AI-Drafted WhatsApp Purchase Orders:** Formats clean, mobile-optimized WhatsApp orders with delivery timelines, urgency tags, and items breakdowns saved to `data/orders/notifications/`.
- **Manager Approval Briefs:** When a PO exceeds `MAX_AUTO_ORDER_LIMIT` (Rs. 50,000), the AI generates an executive decision brief outlining the root-cause demand surge, vendor choice rationale, and stock-out risks.
- **Spending Approval Gates:** Orders exceeding configured spending limits are paused for manager approval rather than auto-dispatching.
- **Dry-run Mode:** Enables verification of all dealer choices and PO formats before touching external APIs.
- **Audit Logging:** Every generated PO is tracked with a unique ID (`PO-YYYYMMDD-XXXX`) in `data/orders/po_log.csv`.
