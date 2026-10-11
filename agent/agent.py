"""Multi-agent orchestrator connecting Festival Scout, Stock Monitor, and Procurement Agent."""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Import deterministic skill runners
run_forecast = importlib.import_module("skills.festival-demand.forecast_demand").run_forecast
run_audit = importlib.import_module("skills.stock-monitor.audit_stock").run_audit
run_optimizer = importlib.import_module("skills.procurement-optimizer.select_dealer").run_optimizer
run_dispatch = importlib.import_module("skills.po-dispatch.dispatch_po").run_dispatch

try:
    import agent.guardrails as guardrails
except ImportError:
    import guardrails


class SupermarketAgentOrchestrator:
    """Coordinates the 3 autonomous agents for full supermarket inventory maintenance."""

    def __init__(self):
        pass

    def run_festival_scout(self, eval_date: str | None = None) -> dict:
        """Agent 1: Festival & Demand Scout."""
        print("\n>>> AGENT 1 [FESTIVAL SCOUT] Running...")
        return run_forecast(eval_date_str=eval_date)

    def run_stock_monitor(self) -> list[dict]:
        """Agent 2: Inventory & Stock Maintenance Monitor."""
        print("\n>>> AGENT 2 [STOCK MONITOR] Running...")
        return run_audit()

    def run_procurement_officer(self, dry_run: bool = False) -> list[dict]:
        """Agent 3: Procurement & Vendor Dispatcher."""
        print("\n>>> AGENT 3 [PROCUREMENT OFFICER] Running...")
        plan = run_optimizer()
        if not plan:
            print("No purchase orders required at this time.")
            return []

        # Validate Guardrails
        for d_id, d_data in plan.items():
            approved, msg = guardrails.check_order_spending_limit(d_data["total_order_value"])
            if not approved:
                print(f"[GUARDRAIL ALERT] for {d_data['dealer_name']}: {msg}")

        # Dispatch
        return run_dispatch(dry_run=dry_run)

    def run_full_lifecycle(self, eval_date: str | None = None, dry_run: bool = False):
        """Execute the end-to-end multi-agent replenishment pipeline."""
        print("=" * 80)
        print(" [STARTING AUTONOMOUS SUPERMARKET INVENTORY REPLENISHMENT CYCLE]")
        print("=" * 80)

        # Step 1: Scout seasonal demand
        self.run_festival_scout(eval_date=eval_date)

        # Step 2: Audit stock with seasonal adjustments
        audit_res = self.run_stock_monitor()

        if not audit_res:
            print("\n[OK] All stock levels healthy. No procurement required.")
            return

        # Step 3: Optimize vendor quotes and dispatch POs
        self.run_procurement_officer(dry_run=dry_run)

        print("\n" + "=" * 80)
        print(" [REPLENISHMENT CYCLE COMPLETED SUCCESSFULLY]")
        print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Supermarket Autonomous Multi-Agent Orchestrator.")
    parser.add_argument("--date", type=str, help="Simulation evaluation date (YYYY-MM-DD)")
    parser.add_argument("--live", action="store_true", help="Execute live dispatch instead of dry-run")
    args = parser.parse_args()

    orchestrator = SupermarketAgentOrchestrator()
    orchestrator.run_full_lifecycle(eval_date=args.date, dry_run=not args.live)
