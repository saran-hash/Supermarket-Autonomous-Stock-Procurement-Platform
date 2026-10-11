"""Deterministic skill to audit supermarket stock and identify reorder deficits."""

from __future__ import annotations

import argparse
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


def run_audit(custom_stock_path: str | None = None) -> list[dict]:
    stock_path = Path(custom_stock_path) if custom_stock_path else storelib.data_path("inventory", "daily_stock.csv")
    multipliers_path = storelib.data_path("calendar", "active_multipliers.json")

    if not stock_path.exists():
        print(f"Error: Inventory file not found at {stock_path}")
        return []

    multipliers = {}
    if multipliers_path.exists():
        try:
            with open(multipliers_path, "r", encoding="utf-8") as f:
                multipliers = json.load(f).get("category_multipliers", {})
        except Exception as e:
            print(f"Warning: Failed to load multipliers: {e}")

    df = pd.read_csv(stock_path)
    requisitions = []

    print("\n==========================================================================================")
    print(" [INVENTORY AUDIT & REORDER CHECK]")
    print("==========================================================================================")
    print(f"{'SKU':<18} | {'Product Name':<25} | {'Stock':<6} | {'Base ROP':<8} | {'Surge':<5} | {'Adj ROP':<7} | {'Action':<10}")
    print("-" * 90)

    for _, row in df.iterrows():
        sku = storelib.norm_sku(str(row["sku_id"]))
        name = str(row["product_name"])
        cat = str(row.get("category", "")).strip()
        current_stock = float(row["current_stock"])
        base_rop = float(row["reorder_point"])
        base_unit = str(row.get("base_unit", "pcs")).strip()
        batch_size = float(row.get("standard_order_batch", base_rop))

        multiplier = float(multipliers.get(cat, 1.0))
        adjusted_rop = round(base_rop * multiplier, 1)

        needs_reorder = current_stock <= adjusted_rop
        status_text = "[REORDER]" if needs_reorder else "[HEALTHY]"

        print(f"{sku:<18} | {name[:25]:<25} | {current_stock:<6.1f} | {base_rop:<8.1f} | {multiplier:<5.1f} | {adjusted_rop:<7.1f} | {status_text:<10}")

        if needs_reorder:
            deficit = max(0.0, adjusted_rop - current_stock)
            recommended_qty = max(batch_size, deficit + (base_rop * 0.5))
            recommended_qty = round(recommended_qty) if base_unit == "pcs" else round(recommended_qty, 1)

            requisitions.append({
                "sku_id": sku,
                "product_name": name,
                "category": cat,
                "current_stock": current_stock,
                "adjusted_rop": adjusted_rop,
                "base_unit": base_unit,
                "deficit": round(deficit, 1),
                "recommended_order_qty": recommended_qty,
            })

    out_file = storelib.data_path("inventory", "reorder_requisitions.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(requisitions, f, indent=2)

    print("-" * 90)
    print(f"Total Low-Stock Items Flagged: {len(requisitions)}")
    print(f"Requisitions written to: {out_file}\n")
    return requisitions


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit supermarket stock levels.")
    parser.add_argument("--stock-file", type=str, help="Custom daily stock CSV path")
    args = parser.parse_args()
    run_audit(args.stock_file)
