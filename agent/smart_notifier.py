"""Smart Notification & Approval Flow Agent for Supermarket Procurement.

Generates human-readable WhatsApp Purchase Orders and executive Manager Approval Briefs
using OpenRouter LLM, backed by robust deterministic fallbacks.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import storelib
from agent.llm_client import call_llm, get_api_key, get_model


def _get_festival_context(as_of_date: str | None = None) -> dict[str, Any] | None:
    """Load active festival multipliers if available."""
    active_path = storelib.data_path("calendar", "active_multipliers.json")
    if active_path.exists():
        try:
            with open(active_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def generate_whatsapp_po_message(
    po_id: str,
    dealer_data: dict[str, Any],
    festival_context: dict[str, Any] | None = None,
) -> str:
    """Draft a professional, vendor-ready WhatsApp Purchase Order message."""
    dealer_name = dealer_data.get("dealer_name", "Valued Supplier")
    items = dealer_data.get("items", [])
    total_val = dealer_data.get("total_order_value", 0.0)

    if festival_context is None:
        festival_context = _get_festival_context()

    active_events = festival_context.get("active_events", []) if festival_context else []
    festival_note = ""
    if active_events:
        ev = active_events[0]
        festival_note = f"Upcoming Event: {ev.get('event')} in {ev.get('days_away')} days."

    # Try generating with LLM
    if get_api_key():
        system_prompt = (
            "You are an automated supermarket procurement officer. "
            "Your task is to draft a clean, professional, courteous WhatsApp Purchase Order message "
            "to a wholesale dealer. Format with WhatsApp markdown (use *bold*, line breaks, emojis). "
            "Keep it crisp, respectful, and easy to read on a mobile phone. "
            "Include: PO Number, Dealer Name, itemized list (qty, unit, price, total), "
            "grand total, delivery urgency, warehouse receiving address, and request for acknowledgement."
        )

        user_prompt = f"""
Draft a WhatsApp Purchase Order with these exact details:
- PO Number: {po_id}
- Supplier: {dealer_name}
- Order Date: {datetime.now().strftime('%d-%b-%Y')}
- Items to Order:
{json.dumps(items, indent=2)}
- Total Order Value: Rs. {total_val:,.2f}
- Context/Urgency: {festival_note or 'Regular weekly inventory restock'}
- Delivery Address: Supermarket Central Inward Hub, Bay #2, Ring Road
- Payment Terms: Standard Credit (Net 15)

Output ONLY the formatted WhatsApp message ready to be sent.
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        llm_response = call_llm(messages, temperature=0.2)
        if llm_response:
            return llm_response

    # Deterministic fallback template
    item_lines = []
    for itm in items:
        item_lines.append(
            f"  • *{itm['product_name']}*: {itm['quantity']} {itm['base_unit']} @ Rs.{itm['unit_price']:,.2f} = *Rs.{itm['total_amount']:,.2f}*"
        )
    items_block = "\n".join(item_lines)

    urgency_block = f"\n⚠️ *Priority Note:* Stock needed before {active_events[0]['event']} (within {active_events[0]['days_away']} days)." if active_events else ""

    return (
        f"🛒 *PURCHASE ORDER: {po_id}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Dear *{dealer_name}*,\n\n"
        f"Please find our official purchase order for immediate dispatch:\n\n"
        f"📅 *Date:* {datetime.now().strftime('%d-%b-%Y')}\n"
        f"📦 *Ordered Items:*\n{items_block}\n\n"
        f"💰 *Net Order Total:* *Rs. {total_val:,.2f}*\n"
        f"📍 *Delivery Destination:* Supermarket Central Inward Hub (Bay #2)\n"
        f"💳 *Payment Terms:* Standard Credit (Net 15){urgency_block}\n\n"
        f"Please reply with *CONFIRM* and your estimated delivery slot.\n"
        f"Thank you,\n"
        f"_Supermarket Automated Procurement Desk_"
    )


def generate_manager_approval_brief(
    po_id: str,
    dealer_data: dict[str, Any],
    spending_limit: float = 50000.0,
    festival_context: dict[str, Any] | None = None,
) -> str:
    """Draft an executive Manager Approval Brief when an order exceeds the auto-dispatch budget."""
    dealer_name = dealer_data.get("dealer_name", "Supplier")
    items = dealer_data.get("items", [])
    total_val = dealer_data.get("total_order_value", 0.0)

    if festival_context is None:
        festival_context = _get_festival_context()

    active_events = festival_context.get("active_events", []) if festival_context else []
    event_str = ", ".join([f"{e.get('event')} ({e.get('multiplier')}x surge in {e.get('days_away')} days)" for e in active_events]) or "Standard replenishment"

    # Try generating with LLM
    if get_api_key():
        system_prompt = (
            "You are an executive procurement intelligence AI for a supermarket retail chain. "
            "An autonomous purchase order exceeded the automatic spending threshold. "
            "Draft a concise, decision-ready Manager Approval Brief for the Store Director. "
            "Break it into clear sections with emojis: "
            "1. 🚨 Financial Alert (PO Value vs Spending Limit) "
            "2. 📈 Root Cause & Surge Trigger (explain festival/season surge) "
            "3. 🤝 Supplier Selection Rationale (why this vendor was chosen) "
            "4. ⚠️ Stock-out Risk of Inaction "
            "5. ✍️ Action Options ([1] Approve Dispatch, [2] Modify Quantities, [3] Reject)."
        )

        user_prompt = f"""
Prepare a Manager Approval Brief for:
- PO Identifier: {po_id}
- Wholesale Dealer: {dealer_name}
- Total Order Value: Rs. {total_val:,.2f}
- Spending Cap: Rs. {spending_limit:,.2f}
- Excess Amount: Rs. {(total_val - spending_limit):,.2f}
- Active Festival / Surge Context: {event_str}
- Order Items Breakdown:
{json.dumps(items, indent=2)}

Format as an executive summary ready for quick mobile/email review.
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        llm_response = call_llm(messages, temperature=0.2)
        if llm_response:
            return llm_response

    # Deterministic fallback executive brief
    excess = total_val - spending_limit
    return (
        f"🚨 *EXECUTIVE PROCUREMENT ALERT: MANAGER APPROVAL REQUIRED*\n"
        f"═════════════════════════════════════════════════════════════════\n"
        f"• *PO Number:* `{po_id}`\n"
        f"• *Assigned Vendor:* *{dealer_name}*\n"
        f"• *Total Order Value:* *Rs. {total_val:,.2f}*\n"
        f"• *Auto-Dispatch Cap:* Rs. {spending_limit:,.2f} (Excess: +Rs. {excess:,.2f})\n\n"
        f"📈 *Root Cause & Demand Driver:*\n"
        f"  Active Surge Trigger: *{event_str}*.\n"
        f"  Reorder thresholds were surge-adjusted to prevent stock-outs across core categories.\n\n"
        f"🤝 *Vendor Selection Rationale:*\n"
        f"  Selected via deterministic optimization (cheapest unit rates meeting MOQ and shortest delivery latency).\n\n"
        f"⚠️ *Operational Risk of Rejection:*\n"
        f"  Rejecting or delaying this PO risks running out of high-velocity inventory during peak holiday footfall.\n\n"
        f"✍️ *Decision Options:*\n"
        f"  [APPROVE] Proceed with automated WhatsApp/Email dispatch to vendor.\n"
        f"  [REVISE]  Trim batch sizes to stay under Rs. {spending_limit:,.2f}.\n"
        f"  [REJECT]  Cancel requisition and absorb stock-out risk.\n"
        f"═════════════════════════════════════════════════════════════════"
    )


def save_notification_artifact(po_id: str, artifact_type: str, content: str) -> Path:
    """Persist generated PO or brief to data/orders/notifications/ for audit trails."""
    notif_dir = storelib.data_path("orders", "notifications")
    notif_dir.mkdir(parents=True, exist_ok=True)
    target_file = notif_dir / f"{po_id}_{artifact_type}.txt"
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(content)
    return target_file
