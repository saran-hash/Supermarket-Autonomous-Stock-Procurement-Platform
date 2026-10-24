"""Unit and integration tests for Smart Notifier & Approval Flow."""

import json
import sys
from pathlib import Path
from unittest.mock import patch
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent.smart_notifier import (
    generate_whatsapp_po_message,
    generate_manager_approval_brief,
    save_notification_artifact,
)


@pytest.fixture
def sample_dealer_order():
    return {
        "dealer_name": "Sri Lakshmi Traders",
        "preferred_channel": "whatsapp",
        "phone_whatsapp": "+919876543210",
        "email": "orders@srilakshmi.com",
        "items": [
            {
                "sku_id": "SKU-OIL-SUN-001",
                "product_name": "Sunflower Oil 1L",
                "base_unit": "pcs",
                "quantity": 90,
                "unit_price": 135.0,
                "total_amount": 12150.0,
                "lead_time_days": 1,
            },
            {
                "sku_id": "SKU-GROC-SUG-001",
                "product_name": "White Refined Sugar 1kg",
                "base_unit": "kg",
                "quantity": 225.0,
                "unit_price": 42.0,
                "total_amount": 9450.0,
                "lead_time_days": 1,
            },
        ],
        "total_order_value": 72400.0,
    }


def test_whatsapp_po_deterministic_fallback(sample_dealer_order):
    """Test that WhatsApp PO message generates clean, structured content even without LLM API key."""
    with patch("agent.smart_notifier.get_api_key", return_value=""):
        msg = generate_whatsapp_po_message("PO-20261025-TEST01", sample_dealer_order)
        assert "PURCHASE ORDER: PO-20261025-TEST01" in msg
        assert "Sri Lakshmi Traders" in msg
        assert "Sunflower Oil 1L" in msg
        assert "Rs. 72,400.00" in msg
        assert "Supermarket Central Inward Hub" in msg


def test_manager_approval_brief_deterministic_fallback(sample_dealer_order):
    """Test that Manager Approval Brief highlights excess budget and key metrics."""
    with patch("agent.smart_notifier.get_api_key", return_value=""):
        brief = generate_manager_approval_brief(
            po_id="PO-20261025-TEST01",
            dealer_data=sample_dealer_order,
            spending_limit=50000.0,
        )
        assert "MANAGER APPROVAL REQUIRED" in brief
        assert "PO-20261025-TEST01" in brief
        assert "Rs. 72,400.00" in brief
        assert "Excess: +Rs. 22,400.00" in brief
        assert "[APPROVE]" in brief


def test_whatsapp_po_with_mocked_llm(sample_dealer_order):
    """Test that when OpenRouter returns content, it is used."""
    mock_ai_output = "🛒 *OFFICIAL PO*\nTo: Sri Lakshmi Traders\nTotal: Rs 72,400\nPlease dispatch ASAP."
    with patch("agent.smart_notifier.get_api_key", return_value="sk-or-fake-key"), \
         patch("agent.smart_notifier.call_llm", return_value=mock_ai_output):
        msg = generate_whatsapp_po_message("PO-20261025-TEST01", sample_dealer_order)
        assert msg == mock_ai_output


def test_save_notification_artifact(tmp_path):
    """Test artifact persistence."""
    saved_file = save_notification_artifact("PO-TEST", "brief", "Test notification content")
    assert saved_file.exists()
    assert saved_file.read_text(encoding="utf-8") == "Test notification content"
