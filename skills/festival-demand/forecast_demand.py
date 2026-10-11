"""Deterministic skill to forecast category surges from calendar festivals."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
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


def run_forecast(eval_date_str: str | None = None, lookahead_days: int = 14) -> dict:
    eval_date = datetime.strptime(eval_date_str, "%Y-%m-%d").date() if eval_date_str else datetime.now().date()
    festivals_csv = storelib.data_path("calendar", "festivals.csv")
    
    if not festivals_csv.exists():
        print(f"Warning: festivals file not found at {festivals_csv}")
        return {}

    df = pd.read_csv(festivals_csv)
    active_surges = {}
    active_events = []

    for _, row in df.iterrows():
        try:
            start_date = datetime.strptime(str(row["start_date"]).strip(), "%Y-%m-%d").date()
        except ValueError:
            continue
        
        days_to_event = (start_date - eval_date).days
        lead_buffer = int(row.get("days_prior_to_stock", 10))

        # Check if today falls in the procurement preparation window
        if 0 <= days_to_event <= max(lead_buffer, lookahead_days):
            event_name = row["event_name"]
            multiplier = float(row.get("surge_multiplier", 1.5))
            target_cats = [c.strip() for c in str(row.get("target_categories", "")).split(",") if c.strip()]
            
            active_events.append({
                "event": event_name,
                "start_date": str(start_date),
                "days_away": days_to_event,
                "multiplier": multiplier,
                "categories": target_cats,
            })

            for cat in target_cats:
                # If multiple events affect the same category, take the maximum multiplier
                active_surges[cat] = max(active_surges.get(cat, 1.0), multiplier)

    out_file = storelib.data_path("calendar", "active_multipliers.json")
    payload = {
        "as_of_date": str(eval_date),
        "active_events": active_events,
        "category_multipliers": active_surges,
    }
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    # Print summary report
    print(f"\n=======================================================")
    print(f" [FESTIVAL DEMAND FORECAST] As of {eval_date}")
    print(f"=======================================================")
    if not active_events:
        print("No high-surge events detected within lookahead window.")
    else:
        for ev in active_events:
            print(f"- Event: {ev['event']} (Starts in {ev['days_away']} days on {ev['start_date']})")
            print(f"  Surge Multiplier: {ev['multiplier']}x across: {', '.join(ev['categories'])}")
    print(f"\nSaved active multipliers to: {out_file}\n")
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Forecast festival demand surges.")
    parser.add_argument("--date", type=str, help="Evaluation date (YYYY-MM-DD)")
    parser.add_argument("--lookahead", type=int, default=14, help="Lookahead window in days")
    args = parser.parse_args()
    run_forecast(args.date, args.lookahead)
