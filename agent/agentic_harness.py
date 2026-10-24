"""Autonomous ReAct / Tool-Calling Agent Harness for Supermarket Replenishment.

Coordinates multi-agent goals through dynamic LLM reasoning and deterministic skill execution.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Generator

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import agent.guardrails as guardrails
from agent.llm_client import call_llm_with_tools, get_api_key, get_model
from agent.tools import AGENT_TOOLS_SCHEMA, execute_tool

SYSTEM_INSTRUCTIONS = """You are the Autonomous Supermarket Replenishment Intelligence Copilot.
You operate a retail chain's inventory, demand forecasting, supplier negotiation, and purchase order systems.

Strict Operating Rules:
1. ZERO CALCULATION HALLUCINATION: Never invent stock deficits, surge multipliers, wholesale costs, or vendor rankings through chat arithmetic. Always call the approved deterministic tools.
2. AGENT SKILLS:
   - Use `forecast_demand` to scan upcoming holidays and compute category surge multipliers.
   - Use `audit_inventory` to detect low-stock items against base and surged reorder points.
   - Use `optimize_procurement` to evaluate wholesale quotes, MOQs, pack sizes, and select best dealers.
   - Use `dispatch_orders` to format AI WhatsApp purchase orders and dispatch them.
   - Use `inspect_stock_levels` or `inspect_dealer_quotes` to inspect specific products on demand.
3. GUARDRAILS: If any Purchase Order total exceeds Rs. 50,000, explicitly highlight this to the Store Manager for approval before completing the cycle.
4. EXPLANATION: Clearly explain your findings, business rationale (e.g. why a vendor was chosen, festival urgency), and order statuses to the Store Manager.
"""


class AgenticSupermarketHarness:
    """Autonomous ReAct loop driving the supermarket multi-agent ecosystem."""

    def __init__(self, model: str | None = None, max_iterations: int = 8):
        self.model = model or get_model()
        self.max_iterations = max_iterations
        self.history: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_INSTRUCTIONS}
        ]

    def _fallback_autonomous_planner(self, goal: str) -> str:
        """Deterministic heuristic fallback planner when LLM API key is not present."""
        print("[HARNESS HEURISTIC PLANNER] Analyzing goal and executing autonomous workflow...")
        goal_lower = goal.lower()
        log = []

        if "festival" in goal_lower or "diwali" in goal_lower or "forecast" in goal_lower or "replenish" in goal_lower or "order" in goal_lower:
            print("  -> Executing: forecast_demand(date='2026-10-25')")
            f_res = json.loads(execute_tool("forecast_demand", {"date": "2026-10-25"}))
            events = [e["event"] for e in f_res.get("active_events", [])]
            log.append(f"• Demand Scout detected upcoming event: {', '.join(events) or 'None'}. Applied category multipliers.")

        if "audit" in goal_lower or "stock" in goal_lower or "replenish" in goal_lower or "order" in goal_lower:
            print("  -> Executing: audit_inventory()")
            a_res = json.loads(execute_tool("audit_inventory", {}))
            count = a_res.get("flagged_items_count", 0)
            log.append(f"• Stock Monitor audited inventory and flagged {count} deficit items needing reorder.")

        if "procure" in goal_lower or "dealer" in goal_lower or "vendor" in goal_lower or "replenish" in goal_lower or "order" in goal_lower:
            print("  -> Executing: optimize_procurement()")
            o_res = json.loads(execute_tool("optimize_procurement", {}))
            val = o_res.get("total_procurement_value", 0.0)
            log.append(f"• Procurement Optimizer selected optimal dealers across {o_res.get('total_suppliers', 0)} vendors. Total spend: Rs. {val:,.2f}.")

        if "dispatch" in goal_lower or "send" in goal_lower or "replenish" in goal_lower or "order" in goal_lower:
            print("  -> Executing: dispatch_orders(dry_run=True)")
            d_res = json.loads(execute_tool("dispatch_orders", {"dry_run": True}))
            log.append(f"• Dispatch Officer drafted AI WhatsApp POs for {d_res.get('dispatched_count', 0)} orders (saved to data/orders/notifications/).")

        report = "\n".join(log)
        return (
            f"✅ **Autonomous Replenishment Cycle Completed (Local Planner)**\n\n"
            f"{report}\n\n"
            f"*Tip: Set `OPENROUTER_API_KEY` in `.env` for free-form multi-turn conversational reasoning.*"
        )

    def run_goal(self, goal: str, verbose: bool = True) -> str:
        """Execute an autonomous goal using LLM tool-calling loop with fallback."""
        if verbose:
            print(f"\n🎯 [GOAL RECEIVED]: \"{goal}\"")
            print("=" * 80)

        api_key = get_api_key()
        if not api_key:
            if verbose:
                print("[NOTE] OPENROUTER_API_KEY not found in .env; switching to autonomous local executor.\n")
            return self._fallback_autonomous_planner(goal)

        self.history.append({"role": "user", "content": goal})

        for step in range(self.max_iterations):
            if verbose:
                print(f"\n--- [AGENTIC ITERATION {step + 1}/{self.max_iterations}] Reasoning & Planning ---")

            response = call_llm_with_tools(
                messages=self.history,
                tools=AGENT_TOOLS_SCHEMA,
                temperature=0.1,
            )

            if not response:
                print("[WARN] LLM API returned empty response, falling back to local executor.")
                return self._fallback_autonomous_planner(goal)

            self.history.append(response)

            tool_calls = response.get("tool_calls", [])
            content = response.get("content")

            if content and verbose:
                print(f"\n🧠 [AGENT THOUGHT]:\n{content}\n")

            if not tool_calls:
                # Finished reasoning and provided final answer
                if verbose:
                    print("=" * 80)
                    print("✅ [GOAL ACCOMPLISHED]")
                return content or "Task finished."

            # Execute tool calls
            for tc in tool_calls:
                fn_name = tc.get("function", {}).get("name", "")
                raw_args = tc.get("function", {}).get("arguments", "{}")
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except Exception:
                    args = {}

                if verbose:
                    print(f"🔧 [INVOKING SKILL]: `{fn_name}` with args: {args}")

                tool_result_str = execute_tool(fn_name, args)

                # Append tool response
                self.history.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", f"call_{fn_name}"),
                    "name": fn_name,
                    "content": tool_result_str,
                })

                if verbose:
                    snippet = tool_result_str[:250] + ("..." if len(tool_result_str) > 250 else "")
                    print(f"   ↳ [SKILL RESULT]: {snippet}")

        return "Reached maximum iteration limit before final completion."
