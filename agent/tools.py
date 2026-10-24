"""Tool definitions and deterministic executors for the Fully Agentic LLM Harness."""

from __future__ import annotations

import glob
import importlib
import json
import sys
from pathlib import Path
from typing import Any
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
import storelib

# Import deterministic skill runners
run_forecast = importlib.import_module("skills.festival-demand.forecast_demand").run_forecast
run_audit = importlib.import_module("skills.stock-monitor.audit_stock").run_audit
run_optimizer = importlib.import_module("skills.procurement-optimizer.select_dealer").run_optimizer
run_dispatch = importlib.import_module("skills.po-dispatch.dispatch_po").run_dispatch


def tool_forecast_demand(date: str = "2026-10-25", lookahead_days: int = 14) -> dict[str, Any]:
    """Scan upcoming festivals and calculate category demand surge multipliers."""
    res = run_forecast(eval_date_str=date, lookahead_days=lookahead_days)
    return {
        "status": "success",
        "eval_date": date,
        "active_events": res.get("active_events", []),
        "category_multipliers": res.get("category_multipliers", {}),
    }


def tool_audit_inventory() -> dict[str, Any]:
    """Audit store inventory against baseline and festival-adjusted reorder points."""
    requisitions = run_audit()
    return {
        "status": "success",
        "flagged_items_count": len(requisitions),
        "requisitions": requisitions,
    }


def tool_optimize_procurement() -> dict[str, Any]:
    """Evaluate wholesale supplier catalogs and select optimal vendors for low-stock items."""
    plan = run_optimizer()
    summary = []
    total_spend = 0.0
    for d_id, data in plan.items():
        total_spend += data.get("total_order_value", 0.0)
        summary.append({
            "dealer_id": d_id,
            "dealer_name": data.get("dealer_name"),
            "items_count": len(data.get("items", [])),
            "order_value": data.get("total_order_value"),
            "preferred_channel": data.get("preferred_channel"),
            "items": data.get("items", []),
        })
    return {
        "status": "success",
        "total_suppliers": len(plan),
        "total_procurement_value": round(total_spend, 2),
        "procurement_plan": summary,
    }


def tool_dispatch_orders(dry_run: bool = True) -> dict[str, Any]:
    """Format AI WhatsApp POs and dispatch purchase orders to suppliers."""
    orders = run_dispatch(dry_run=dry_run)
    return {
        "status": "success",
        "mode": "simulation" if dry_run else "live",
        "dispatched_count": len(orders),
        "orders": orders,
    }


def tool_inspect_stock_levels(product_or_sku: str = "") -> dict[str, Any]:
    """Inspect current warehouse and on-shelf stock counts for a product or category."""
    stock_file = storelib.data_path("inventory", "daily_stock.csv")
    if not stock_file.exists():
        return {"status": "error", "message": "daily_stock.csv not found"}
    df = pd.read_csv(stock_file)
    if product_or_sku:
        query = product_or_sku.lower()
        matched = df[df["product_name"].str.lower().str.contains(query) | 
                     df["sku_id"].str.lower().str.contains(query) |
                     df["category"].str.lower().str.contains(query)]
    else:
        matched = df
    return {
        "status": "success",
        "matched_count": len(matched),
        "items": matched.to_dict(orient="records"),
    }


def tool_inspect_dealer_quotes(product_or_sku: str = "") -> dict[str, Any]:
    """Inspect supplier price lists, MOQs, pack sizes, and delivery latency."""
    price_dir = storelib.data_path("dealers", "price_lists")
    dealer_master = storelib.data_path("dealers", "dealer_master.csv")
    dealers_df = pd.read_csv(dealer_master).set_index("dealer_id") if dealer_master.exists() else None

    target_sku = storelib.norm_sku(product_or_sku) if product_or_sku else ""
    quotes = []

    for f in glob.glob(str(price_dir / "*.csv")):
        d_id = Path(f).stem
        pdf = pd.read_csv(f)
        if target_sku:
            pdf = pdf[pdf["sku_id"] == target_sku]
        for _, row in pdf.iterrows():
            d_name = dealers_df.loc[d_id]["dealer_name"] if dealers_df is not None and d_id in dealers_df.index else d_id
            quotes.append({
                "dealer_id": d_id,
                "dealer_name": d_name,
                "sku_id": row["sku_id"],
                "unit_price": row["unit_price"],
                "moq": row.get("min_order_qty", 1),
                "pack_size": row.get("pack_size", ""),
                "lead_time_days": row.get("lead_time_days", 3),
            })
    return {
        "status": "success",
        "target_sku": target_sku,
        "quotes": quotes,
    }


# Map tool name string to callable function
TOOL_REGISTRY = {
    "forecast_demand": tool_forecast_demand,
    "audit_inventory": tool_audit_inventory,
    "optimize_procurement": tool_optimize_procurement,
    "dispatch_orders": tool_dispatch_orders,
    "inspect_stock_levels": tool_inspect_stock_levels,
    "inspect_dealer_quotes": tool_inspect_dealer_quotes,
}

# OpenAI/OpenRouter compliant Tool Definitions schema
AGENT_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "forecast_demand",
            "description": "Scans the festival and holiday calendar for upcoming events and calculates category demand surge multipliers (e.g., Diwali surge on Edible Oils and Staples).",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Simulation target date (YYYY-MM-DD), e.g. '2026-10-25'",
                    },
                    "lookahead_days": {
                        "type": "integer",
                        "description": "Number of days ahead to scan for festivals (default: 14)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "audit_inventory",
            "description": "Audits on-shelf and backroom supermarket stock against normal and festival-adjusted reorder points (ROP). Flags all deficit items.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "optimize_procurement",
            "description": "Evaluates all wholesale dealer price sheets, Minimum Order Quantities (MOQ), and delivery lead times to select the optimal supplier for low-stock items.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "dispatch_orders",
            "description": "Formats and dispatches Purchase Orders (POs) to suppliers via WhatsApp or Email. Creates AI-drafted messages and audit logs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dry_run": {
                        "type": "boolean",
                        "description": "If True, simulates dispatch and saves PO artifacts without hitting external APIs. Defaults to True.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_stock_levels",
            "description": "Queries current warehouse inventory count, base units, and threshold levels for a given product name, SKU, or category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_or_sku": {
                        "type": "string",
                        "description": "Name or SKU of product (e.g. 'Basmati Rice', 'Sunflower Oil', or 'Staples'). Leave empty for all.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_dealer_quotes",
            "description": "Queries wholesale price quotes, MOQ requirements, pack sizes, and lead times across dealers for a specific product.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_or_sku": {
                        "type": "string",
                        "description": "Product name or SKU to inspect quotes for (e.g. 'Sugar', 'Sunflower Oil').",
                    }
                },
                "required": ["product_or_sku"],
            },
        },
    },
]


def execute_tool(tool_name: str, args: dict[str, Any]) -> str:
    """Execute a registered tool deterministically and return JSON string result."""
    func = TOOL_REGISTRY.get(tool_name)
    if not func:
        return json.dumps({"status": "error", "message": f"Unknown tool: {tool_name}"})
    try:
        result = func(**args)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
