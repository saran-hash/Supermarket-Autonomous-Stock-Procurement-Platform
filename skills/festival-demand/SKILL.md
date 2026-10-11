---
name: festival-demand
description: Scans upcoming cultural, public holidays, and seasonal events within a lookahead window, calculating category-specific demand surge multipliers and writing active safety-stock overrides.
---

# Festival & Seasonal Demand Forecasting

## Usage
```bash
python skills/festival-demand/forecast_demand.py [--date YYYY-MM-DD] [--lookahead DAYS]
```

## Flags
- `--date`: Target date to evaluate from (default: today).
- `--lookahead`: Days to scan ahead for upcoming festivals (default: 14).
