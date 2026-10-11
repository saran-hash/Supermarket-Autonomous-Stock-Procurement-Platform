"""Safety policies, budget authorization gates, and sandboxing."""

from __future__ import annotations

import re
from typing import Tuple

# Maximum total value of a single Purchase Order that can be auto-dispatched
MAX_AUTO_ORDER_LIMIT = 50000.0  # Rs. 50,000

# Prohibited shell tokens to prevent arbitrary code execution or data destruction
FORBIDDEN_COMMANDS = {
    "rm", "del", "erase", "format", "shutdown", "drop", "truncate", "chmod", "chown"
}


def check_order_spending_limit(order_value: float) -> Tuple[bool, str]:
    """Verify if a Purchase Order exceeds automated spending limits."""
    if order_value > MAX_AUTO_ORDER_LIMIT:
        return (
            False,
            f"HIGH_VALUE_THRESHOLD: PO value of Rs.{order_value:,.2f} exceeds auto-order cap of Rs.{MAX_AUTO_ORDER_LIMIT:,.2f}. Human approval required."
        )
    return (True, "Approved for automated dispatch.")


def validate_command(cmd_str: str) -> bool:
    """Ensure agent execution does not invoke destructive system operations."""
    tokens = re.findall(r"\b\w+\b", cmd_str.lower())
    for t in tokens:
        if t in FORBIDDEN_COMMANDS:
            return False
    return True
