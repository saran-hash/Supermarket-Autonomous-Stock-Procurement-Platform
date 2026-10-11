---
name: stock-monitor
description: Audits on-shelf and warehouse supermarket inventory against baseline and festival-adjusted reorder thresholds, calculating deficits and generating reorder requisitions.
---

# Supermarket Stock Monitor

## Usage
```bash
python skills/stock-monitor/audit_stock.py [--stock-file PATH]
```

## Description
Cross-references `inventory/daily_stock.csv` with active seasonal multipliers (`calendar/active_multipliers.json`) to detect shortages and calculate exact batch reorder requisitions.
