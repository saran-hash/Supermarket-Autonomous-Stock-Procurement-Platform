"""Context builder that loads AGENTS.md, Data Catalog, and role prompts."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
import storelib

AGENTS_MD_PATH = REPO_ROOT / "AGENTS.md"
CATALOG_PATH = storelib.code_path("catalog", "DATA_CATALOG.md")


def load_base_rules() -> str:
    rules = ""
    if AGENTS_MD_PATH.exists():
        rules += AGENTS_MD_PATH.read_text(encoding="utf-8")
    return rules


FESTIVAL_AGENT_PROMPT = """
Role: Festival & Seasonal Demand Scout (FestivalDemandAgent)
Mission: You analyze calendar dates and local events to forecast product demand surges.
Always use skills/festival-demand/forecast_demand.py for deterministic calculations.
Never calculate surge factors through text hallucination.
"""

STOCK_MONITOR_PROMPT = """
Role: Supermarket Stock Maintenance Monitor (StockMonitorAgent)
Mission: You audit current stock levels against base and festival-adjusted reorder points.
Always use skills/stock-monitor/audit_stock.py for deterministic inventory audits.
"""

PROCUREMENT_AGENT_PROMPT = """
Role: Wholesale Purchasing & PO Dispatcher (ProcurementAgent)
Mission: You select the optimal wholesale dealer based on price, lead time, and rating, and dispatch POs.
Always use skills/procurement-optimizer/select_dealer.py and skills/po-dispatch/dispatch_po.py.
Respect spending limits defined in guardrails.py.
"""
