"""Interactive CLI Copilot for the Supermarket Autonomous Stock & Procurement Platform."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from agent.agentic_harness import AgenticSupermarketHarness
from agent.llm_client import get_api_key, get_model


def run_interactive_copilot():
    """Start interactive REPL chat session with the autonomous agent."""
    harness = AgenticSupermarketHarness()
    api_key = get_api_key()
    model = get_model()

    print("\n" + "=" * 80)
    print(" 🛒 SUPERMARKET AUTONOMOUS PROCUREMENT COPILOT")
    print("=" * 80)
    print(f"• Active Model: {model}")
    print(f"• OpenRouter API Key: {'[CONFIGURED]' if api_key else '[NOT DETECTED - USING LOCAL PLANNER]'}")
    print("• Type your command or question (e.g. 'Check inventory for Diwali', 'Inspect Sugar quotes', or 'exit')\n")

    while True:
        try:
            user_input = input("Store Manager >> ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("\nExiting Copilot. Good day!\n")
                break

            response = harness.run_goal(user_input, verbose=True)
            print("\n" + response + "\n")
            print("-" * 80)
        except (KeyboardInterrupt, EOFError):
            print("\nSession ended.\n")
            break


def main():
    parser = argparse.ArgumentParser(description="Run autonomous supermarket copilot.")
    parser.add_argument("goal", nargs="?", type=str, help="Specific goal or question for the copilot")
    parser.add_argument("--interactive", "-i", action="store_true", help="Launch interactive chat session")
    args = parser.parse_args()

    if args.goal:
        harness = AgenticSupermarketHarness()
        answer = harness.run_goal(args.goal, verbose=True)
        print("\n" + answer + "\n")
    else:
        run_interactive_copilot()


if __name__ == "__main__":
    main()
