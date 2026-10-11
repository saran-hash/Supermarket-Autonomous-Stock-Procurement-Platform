---
name: procurement-optimizer
description: Evaluates dealer catalogues, price lists, MOQs, lead times, and ratings across all available vendors to select the optimal dealer and generate a consolidated procurement plan.
---

# Procurement Optimizer

## Usage
```bash
python skills/procurement-optimizer/select_dealer.py
```

## Description
Cross-references requisitions from `inventory/reorder_requisitions.json` against all active dealer price lists in `dealers/price_lists/` to select the best vendor per item using a multi-criteria scoring algorithm.
