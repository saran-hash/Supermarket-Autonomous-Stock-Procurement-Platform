---
name: po-dispatch
description: Formats formal Purchase Orders (POs) from the procurement plan, selects communication channel (WhatsApp / Email), dispatches the orders, and writes audit logs to po_log.csv.
---

# Purchase Order Dispatch

## Usage
```bash
python skills/po-dispatch/dispatch_po.py [--dry-run]
```

## Flags
- `--dry-run`: Generates POs and logs without executing external network calls (default: False).
