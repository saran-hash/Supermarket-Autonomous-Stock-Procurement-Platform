# Supermarket Semantic Data Catalog

Reference specification for all data tables, schemas, relations, and grain definitions across the supermarket platform.

---

## 📊 Summary of Datasets

| Dataset | Relative Path | Grain | Primary Join Key | Description |
|---|---|---|---|---|
| **Daily Stock** | `inventory/daily_stock.csv` | 1 row per SKU | `sku_id` | Current store inventory levels, safety thresholds, and reorder points. |
| **Dealer Master** | `dealers/dealer_master.csv` | 1 row per Dealer | `dealer_id` | Supplier contact directory, preferred dispatch channel, and rating. |
| **Price Lists** | `dealers/price_lists/<dealer_id>.csv` | 1 row per (Dealer, SKU) | `(dealer_id, sku_id)` | Wholesale unit pricing, Minimum Order Quantity (MOQ), pack size, lead time. |
| **Festival Calendar** | `calendar/festivals.csv` | 1 row per Event | `event_name` | Upcoming festivals, affected product categories, and demand surge multipliers. |
| **Purchase Order Log** | `orders/po_log.csv` | 1 row per PO Line | `po_id` | Audit trail of all generated, approved, and dispatched purchase orders. |

---

## 1. Daily Stock (`inventory/daily_stock.csv`)

Tracks on-shelf and backroom store inventory. Updated daily or after POS closing shift.

- **`sku_id`** *(string, PK)*: Canonical SKU identifier (e.g. `SKU-OIL-SUN-001`).
- **`product_name`** *(string)*: Human-readable product title.
- **`category`** *(string)*: Product department (`Edible Oils`, `Staples`, `Dairy & Ghee`, `Dry Fruits`).
- **`current_stock`** *(float)*: Current quantity on hand in `base_unit`.
- **`base_unit`** *(string)*: Measurement unit (`pcs`, `kg`, `L`).
- **`min_safety_stock`** *(float)*: Absolute minimum buffer level.
- **`reorder_point`** *(float)*: Threshold where replenishment is triggered.
- **`standard_order_batch`** *(float)*: Standard reorder quantity when ordering.
- **`lead_time_days`** *(int)*: Standard supplier replenishment latency.

---

## 2. Dealer Master (`dealers/dealer_master.csv`)

Supplier directory containing contact points and channel preferences.

- **`dealer_id`** *(string, PK)*: Canonical supplier identifier (e.g. `DLR-001`).
- **`dealer_name`** *(string)*: Registered company / trade name.
- **`contact_person`** *(string)*: Sales manager or representative name.
- **`preferred_channel`** *(string)*: `whatsapp` or `email`.
- **`phone_whatsapp`** *(string)*: International E.164 phone number for WhatsApp Cloud API.
- **`email`** *(string)*: Order dispatch email address.
- **`payment_terms`** *(string)*: Trade credit term (e.g. `Net 15`, `Net 30`, `COD`).
- **`rating`** *(float, 1.0 - 5.0)*: Supplier reliability and fulfillment score.

---

## 3. Dealer Price Lists (`dealers/price_lists/<dealer_id>.csv`)

Item catalog provided by each individual wholesale vendor.

- **`sku_id`** *(string, FK)*: Canonical SKU identifier.
- **`unit_price`** *(float)*: Wholesale price per base unit in local currency (₹).
- **`min_order_qty`** *(float)*: Minimum order quantity (MOQ) required by the vendor.
- **`pack_size`** *(string)*: Packaging standard (e.g. `15 pcs/box`, `50 kg/bag`).
- **`lead_time_days`** *(int)*: Quoted delivery latency.
- **`in_stock`** *(boolean)*: Vendor availability status.

---

## 4. Festival & Event Calendar (`calendar/festivals.csv`)

Seasonal event calendar mapping upcoming cultural and public events to category demand surges.

- **`event_name`** *(string)*: Event title (e.g. `Diwali`, `Pongal`, `Eid`).
- **`start_date`** *(date, YYYY-MM-DD)*: Event commencement date.
- **`end_date`** *(date, YYYY-MM-DD)*: Event end date.
- **`target_categories`** *(string, comma-separated)*: Categories experiencing demand spikes.
- **`surge_multiplier`** *(float)*: Buffer factor (e.g. `2.5` means 250% of standard ROP).
- **`days_prior_to_stock`** *(int)*: How many days in advance the supermarket must order.

---

## 5. Purchase Order Log (`orders/po_log.csv`)

Append-only record of all generated purchase orders.

- **`po_id`** *(string, PK)*: Unique identifier formatted as `PO-YYYYMMDD-XXXX`.
- **`po_date`** *(date, YYYY-MM-DD)*: Generation timestamp.
- **`dealer_id`** *(string, FK)*: Supplier receiving the PO.
- **`sku_id`** *(string, FK)*: Ordered item.
- **`quantity`** *(float)*: Ordered quantity.
- **`unit`** *(string)*: Packaging / base unit.
- **`unit_price`** *(float)*: Agreed price per unit.
- **`total_amount`** *(float)*: Total cost for this line item.
- **`channel_dispatched`** *(string)*: `whatsapp`, `email`, or `dry-run`.
- **`dispatch_status`** *(string)*: `PENDING`, `DISPATCHED`, `DELIVERED`, `FLAGGED_HIGH_VALUE`.
