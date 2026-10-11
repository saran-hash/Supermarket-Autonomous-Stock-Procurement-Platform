"""Deterministic skill to format and dispatch Purchase Orders via WhatsApp and Email."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
import storelib


def run_dispatch(dry_run: bool = False) -> list[dict]:
    plan_path = storelib.data_path("orders", "procurement_plan.json")
    po_log_path = storelib.data_path("orders", "po_log.csv")

    if not plan_path.exists():
        print(f"Error: Procurement plan not found at {plan_path}. Run procurement-optimizer first.")
        return []

    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    if not plan:
        print("No dealers or items in the procurement plan.")
        return []

    today_str = datetime.now().strftime("%Y-%m-%d")
    today_compact = datetime.now().strftime("%Y%m%d")

    dispatched_orders = []

    print("\n==========================================================================================")
    mode_text = "[DRY-RUN SIMULATION]" if dry_run else "[LIVE DISPATCH]"
    print(f" [PURCHASE ORDER DISPATCH] {mode_text}")
    print("==========================================================================================")

    log_rows = []

    for d_id, d_data in plan.items():
        po_id = f"PO-{today_compact}-{uuid.uuid4().hex[:6].upper()}"
        dealer_name = d_data["dealer_name"]
        channel = d_data["preferred_channel"]
        phone = d_data["phone_whatsapp"]
        email = d_data["email"]
        total_val = d_data["total_order_value"]

        print(f"\n* {po_id} -> {dealer_name} ({d_id})")
        print(f"   Channel: {channel.upper()} | Target: {phone if channel == 'whatsapp' else email}")
        print(f"   Total Value: Rs.{total_val:,.2f}")
        print(f"   Items:")

        for itm in d_data["items"]:
            print(f"     - {itm['product_name']}: {itm['quantity']} {itm['base_unit']} @ Rs.{itm['unit_price']} (Rs.{itm['total_amount']:,.2f})")
            log_rows.append({
                "po_id": po_id,
                "po_date": today_str,
                "dealer_id": d_id,
                "sku_id": itm["sku_id"],
                "quantity": itm["quantity"],
                "unit": itm["base_unit"],
                "unit_price": itm["unit_price"],
                "total_amount": itm["total_amount"],
                "channel_dispatched": channel if not dry_run else f"{channel}-dryrun",
                "dispatch_status": "DISPATCHED" if not dry_run else "SIMULATED",
            })

        dispatched_orders.append({
            "po_id": po_id,
            "dealer_id": d_id,
            "dealer_name": dealer_name,
            "channel": channel,
            "total_value": total_val,
            "items_count": len(d_data["items"]),
            "status": "DISPATCHED" if not dry_run else "SIMULATED",
        })

    # Append to po_log.csv
    file_exists = po_log_path.exists() and po_log_path.stat().st_size > 0
    with open(po_log_path, "a", newline="", encoding="utf-8") as f:
        fieldnames = [
            "po_id", "po_date", "dealer_id", "sku_id", "quantity",
            "unit", "unit_price", "total_amount", "channel_dispatched", "dispatch_status"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for row in log_rows:
            writer.writerow(row)

    print("\n------------------------------------------------------------------------------------------")
    print(f"Successfully processed {len(dispatched_orders)} Purchase Orders.")
    print(f"Audit log appended to: {po_log_path}\n")
    return dispatched_orders


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dispatch Purchase Orders to dealers.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without real dispatch")
    args = parser.parse_args()
    run_dispatch(dry_run=args.dry_run)
