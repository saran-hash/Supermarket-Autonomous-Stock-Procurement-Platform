"""Deterministic skill to score wholesale dealers and generate procurement plans."""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path
import pandas as pd

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
import storelib


def run_optimizer() -> dict:
    req_path = storelib.data_path("inventory", "reorder_requisitions.json")
    dealer_master_path = storelib.data_path("dealers", "dealer_master.csv")
    price_dir = storelib.data_path("dealers", "price_lists")

    if not req_path.exists():
        print(f"No requisitions found at {req_path}. Run stock-monitor audit first.")
        return {}

    with open(req_path, "r", encoding="utf-8") as f:
        requisitions = json.load(f)

    if not requisitions:
        print("No items flagged for reorder.")
        return {}

    dealers_df = pd.read_csv(dealer_master_path).set_index("dealer_id")

    dealer_quotes = []
    for f in glob.glob(str(price_dir / "*.csv")):
        d_id = Path(f).stem
        pdf = pd.read_csv(f)
        pdf["dealer_id"] = d_id
        dealer_quotes.append(pdf)

    if not dealer_quotes:
        print(f"Error: No price lists found in {price_dir}")
        return {}

    quotes_df = pd.concat(dealer_quotes, ignore_index=True)

    procurement_plan = {}
    print("\n==========================================================================================")
    print(" [PROCUREMENT OPTIMIZER] VENDOR SELECTION & PRICING")
    print("==========================================================================================")

    for item in requisitions:
        sku = item["sku_id"]
        qty_needed = item["recommended_order_qty"]

        item_quotes = quotes_df[quotes_df["sku_id"] == sku].copy()
        if item_quotes.empty:
            print(f"- Warning: No dealer quotes found for {sku} ({item['product_name']})")
            continue

        best_quote = None
        best_score = float("inf")

        for _, q in item_quotes.iterrows():
            d_id = q["dealer_id"]
            if d_id not in dealers_df.index:
                continue

            d_info = dealers_df.loc[d_id]
            unit_price = float(q["unit_price"])
            moq = float(q.get("min_order_qty", 1.0))
            lead_time = int(q.get("lead_time_days", 3))
            rating = float(d_info.get("rating", 4.0))

            final_qty = max(qty_needed, moq)
            score = (unit_price * 1.0) + (lead_time * 2.0) - (rating * 5.0)

            if score < best_score:
                best_score = score
                best_quote = {
                    "dealer_id": d_id,
                    "dealer_name": d_info["dealer_name"],
                    "preferred_channel": storelib.norm_channel(d_info.get("preferred_channel", "email")),
                    "phone_whatsapp": str(d_info.get("phone_whatsapp", "")),
                    "email": str(d_info.get("email", "")),
                    "unit_price": unit_price,
                    "moq": moq,
                    "final_order_qty": final_qty,
                    "total_amount": round(final_qty * unit_price, 2),
                    "lead_time_days": lead_time,
                    "rating": rating,
                }

        if best_quote:
            d_id = best_quote["dealer_id"]
            if d_id not in procurement_plan:
                procurement_plan[d_id] = {
                    "dealer_name": best_quote["dealer_name"],
                    "preferred_channel": best_quote["preferred_channel"],
                    "phone_whatsapp": best_quote["phone_whatsapp"],
                    "email": best_quote["email"],
                    "items": [],
                    "total_order_value": 0.0,
                }

            line_item = {
                "sku_id": sku,
                "product_name": item["product_name"],
                "base_unit": item["base_unit"],
                "quantity": best_quote["final_order_qty"],
                "unit_price": best_quote["unit_price"],
                "total_amount": best_quote["total_amount"],
                "lead_time_days": best_quote["lead_time_days"],
            }
            procurement_plan[d_id]["items"].append(line_item)
            procurement_plan[d_id]["total_order_value"] += best_quote["total_amount"]

            print(f"- {item['product_name'][:25]} -> Assigned to {best_quote['dealer_name']} ({d_id})")
            print(f"  Qty: {best_quote['final_order_qty']} {item['base_unit']} @ Rs.{best_quote['unit_price']} | Total: Rs.{best_quote['total_amount']:,.2f} | Delivery: {best_quote['lead_time_days']} days")

    for d_id, d_data in procurement_plan.items():
        d_data["total_order_value"] = round(d_data["total_order_value"], 2)

    out_file = storelib.data_path("orders", "procurement_plan.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(procurement_plan, f, indent=2)

    print("-" * 90)
    print(f"Procurement plan consolidated for {len(procurement_plan)} dealers.")
    print(f"Saved to: {out_file}\n")
    return procurement_plan


if __name__ == "__main__":
    run_optimizer()
