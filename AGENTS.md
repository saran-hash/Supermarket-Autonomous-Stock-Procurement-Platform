# Supermarket Autonomous Stock & Procurement Operating Rules

Canonical operating rules and agent contracts for the Supermarket Autonomous Stock & Procurement Platform.

---

## 🧱 Code vs. Data Separation

This repository contains **code only**. Transactional data (daily stock snapshots, POS transactions, dealer master lists, price catalogs, and PO logs) lives in an independent data directory referenced by `STORE_DATA_ROOT` (defaults to `./data` if unset).

- **Code paths:** Use `storelib.code_path(*parts)` for referencing internal scripts or configs.
- **Data paths:** Use `storelib.data_path(*parts)` for reading/writing inventory, dealer lists, or generated orders.

---

## 🔑 Canonical Normalization & Join Keys (`storelib.py`)

Supermarket datasets often describe items, quantities, and dealers with inconsistent casing, abbreviations, or units. All scripts and agents MUST pass data through the canonical normalizers in `storelib.py`:

| Domain | Raw Examples | Canonical Format | Normalizer Function |
|---|---|---|---|
| **SKU / Item** | `Sunflower Oil 1L`, `Oil-Sunflower-1000ml`, `8901234567890` | `SKU-OIL-SUN-001` | `storelib.norm_sku(val)` |
| **Quantity** | `1000g`, `5 kg`, `12 pcs`, `2 boxes` | `(float_qty, base_unit)` | `storelib.norm_qty(val, unit)` |
| **Dealer** | `Sri Lakshmi Traders`, `DLR-001`, `dealer_01` | `DLR-001` | `storelib.norm_dealer(val)` |
| **Channel** | `whatsapp`, `WA`, `mail`, `email` | `whatsapp` or `email` | `storelib.norm_channel(val)` |

---

## 🤖 The Tri-Agent Ecosystem

### Agent 1: Festival & Demand Scout (`FestivalDemandAgent`)
- **Mission:** Monitor upcoming calendar dates, festivals, holidays, and weather anomalies.
- **Trigger:** Daily morning schedule or on-demand query.
- **Skills Used:** `skills/festival-demand/forecast_demand.py`
- **Output Contract:** Emits category demand multipliers (e.g. `{"Edible Oils": 2.5, "Staples": 2.0}`) and writes dynamic thresholds to `data/calendar/active_multipliers.json`.
- **Handoff:** Alerts `StockMonitorAgent` to evaluate stock against the surged reorder points.

### Agent 2: Inventory & Stock Maintenance Monitor (`StockMonitorAgent`)
- **Mission:** Continually evaluate store stock counts against normal and festival-adjusted Reorder Points (ROP).
- **Trigger:** Scheduled 2-hour cron, POS batch sync, or handoff from `FestivalDemandAgent`.
- **Skills Used:** `skills/stock-monitor/audit_stock.py`
- **Logic:**
  $$\text{Adjusted ROP} = \text{Base ROP} \times \text{Festival Multiplier}$$
  $$\text{Deficit} = \text{Adjusted ROP} - \text{Current Stock}$$
- **Output Contract:** Generates a structured reorder requisition list (`temp/reorder_requisitions.json`) for items where `Current Stock <= Adjusted ROP`.
- **Handoff:** Hands off requisitions to `ProcurementAgent`.

### Agent 3: Procurement & Vendor Dispatcher (`ProcurementAgent`)
- **Mission:** Select the optimal supplier for low-stock items and dispatch formal Purchase Orders.
- **Trigger:** Reorder requisition handoff from `StockMonitorAgent` or manual manager command.
- **Skills Used:**
  - `skills/procurement-optimizer/select_dealer.py` (determines optimal dealer per SKU based on price, MOQ, pack size, lead time, and dealer reliability score).
  - `skills/po-dispatch/dispatch_po.py` (builds PO PDF, checks dealer's preferred channel, sends via WhatsApp Cloud API or Email, and logs to `data/orders/po_log.csv`).
- **Safety Gate:** If a single PO value exceeds `MAX_AUTO_ORDER_AMOUNT` (default: ₹50,000 / $600), the agent flags the order for human confirmation rather than dispatching immediately.

---

## 🛠️ Deterministic Skills Policy

1. **No Arithmetic in System Prompts:** Agents must never estimate batch costs, calculate deficits, or pick lowest-cost vendors through chat generation.
2. **Deterministic Script Execution:** Agents formulate CLI arguments, execute the approved skill, inspect the generated CSV/JSON results, and explain the findings to the store manager.
3. **Audit Trail:** Every action that mutates order state or dispatches an external message must append an entry to `data/orders/po_log.csv`.
