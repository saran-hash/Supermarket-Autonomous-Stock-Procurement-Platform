"""Root entrypoint to run end-to-end supermarket multi-agent replenishment."""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent.agent import SupermarketAgentOrchestrator

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run autonomous replenishment pipeline.")
    parser.add_argument("--date", type=str, default="2026-10-25", help="Simulation date (YYYY-MM-DD)")
    parser.add_argument("--live", action="store_true", help="Enable live PO dispatch")
    args = parser.parse_args()

    orchestrator = SupermarketAgentOrchestrator()
    orchestrator.run_full_lifecycle(eval_date=args.date, dry_run=not args.live)
