"""Tests for the Fully Agentic LLM Harness and Tool Registry."""

import json
import sys
from pathlib import Path
from unittest.mock import patch
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent.tools import execute_tool, AGENT_TOOLS_SCHEMA
from agent.agentic_harness import AgenticSupermarketHarness


def test_tool_schema_definitions():
    """Verify tool schemas conform to function calling specifications."""
    assert len(AGENT_TOOLS_SCHEMA) >= 4
    names = [t["function"]["name"] for t in AGENT_TOOLS_SCHEMA]
    assert "forecast_demand" in names
    assert "audit_inventory" in names
    assert "optimize_procurement" in names
    assert "dispatch_orders" in names


def test_execute_inspect_stock():
    """Test inspecting stock levels for a specific product."""
    res = json.loads(execute_tool("inspect_stock_levels", {"product_or_sku": "Sugar"}))
    assert res["status"] == "success"
    assert res["matched_count"] >= 1
    assert any("Sugar" in item["product_name"] for item in res["items"])


def test_fallback_planner_run():
    """Test autonomous goal execution via local fallback planner."""
    harness = AgenticSupermarketHarness()
    with patch("agent.agentic_harness.get_api_key", return_value=""):
        result = harness.run_goal("Check Diwali inventory and replenish stock", verbose=False)
        assert "Autonomous Replenishment Cycle Completed" in result
        assert "Demand Scout" in result
        assert "Stock Monitor" in result


def test_mocked_llm_tool_calling_loop():
    """Test multi-turn ReAct tool execution with a simulated LLM tool-calling response."""
    harness = AgenticSupermarketHarness()

    step1_response = {
        "role": "assistant",
        "content": "I need to inspect the stock levels for Sugar first.",
        "tool_calls": [
            {
                "id": "call_123",
                "type": "function",
                "function": {
                    "name": "inspect_stock_levels",
                    "arguments": json.dumps({"product_or_sku": "Sugar"}),
                },
            }
        ],
    }

    step2_response = {
        "role": "assistant",
        "content": "Sugar stock is currently at 45kg, which is below our safety margin.",
        "tool_calls": [],
    }

    with patch("agent.agentic_harness.get_api_key", return_value="sk-or-fake-key"), \
         patch("agent.agentic_harness.call_llm_with_tools", side_effect=[step1_response, step2_response]):
        final_answer = harness.run_goal("What is the current stock of Sugar?", verbose=False)
        assert "Sugar stock is currently at 45kg" in final_answer
        assert len(harness.history) >= 4  # System + User + Assistant(tool_call) + Tool_result + Assistant(final)
