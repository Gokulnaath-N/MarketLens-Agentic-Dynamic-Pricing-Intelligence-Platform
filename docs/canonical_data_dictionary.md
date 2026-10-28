# MarketLens AI — Canonical Data Dictionary

**Document Version:** 1.0.0  
**Phase:** Phase 2 (Canonical Modeling & Demand Forecasting)  
**Status:** Approved & Implemented  
**Date:** 2026-10-28  

---

## 1. Overview

MarketLens AI decouples source-specific raw transactional formats from downstream analytics and machine learning through a strict, validated canonical schema architecture.

Raw inputs (such as the UCI Online Retail II dataset) undergo format normalization, boundary cleansing, and namespaced entity mapping to produce three canonical tabular structures stored in columnar Parquet format:
1. **Canonical Sales Observations** (`sales_observations.parquet`)
2. **Aggregated Demand Time-Series** (`demand_timeseries.parquet`)
3. **Canonical Product Catalog** (`product_catalog.parquet`)

All schemas are enforced programmatically in Python via [contracts.py](file:///d:/Professional%20Projects/Agentic_Dynammic_Intelligence_Platform/src/marketlens/data/contracts.py).

---

## 2. Table: Canonical Sales Observations (`sales_observations`)

Individual transaction line items representing successful completed retail customer sales.

| Column Name | Data Type | Nullable | Source Column (UCI) | Semantic Description |
| :--- | :--- | :--- | :--- | :--- |
| `transaction_id` | `string` | No | `Invoice` | Unique transaction or invoice identifier. Cleaned of cancellation flags (`C`). |
| `product_id` | `string` | No | `StockCode` | Namespaced canonical product identifier (e.g. `uci_85123A`). |
| `sales_timestamp` | `timestamp[ns]` | No | `InvoiceDate` | Date and time the transaction was recorded (UTC/local timestamp). |
| `units_sold` | `int64` | No | `Quantity` | Non-negative integer quantity of units purchased in this line item ($Q > 0$). |
| `unit_price` | `float64` | No | `Price` | Transactional unit price in British Pounds (£). Non-negative and non-zero ($P > 0$). |
| `customer_id` | `string` | Yes | `Customer ID` | Anonymized unique customer ID. Nullable for guest checkouts. |
| `country` | `string` | Yes | `Country` | Country name of the purchasing customer. |
| `currency` | `string` | No | *(Assigned)* | ISO 4217 currency code. Defaults to `"GBP"` for UCI Online Retail. |

### Exclusion & Cleansing Policy
- **Cancellations:** Invoices starting with `'C'` or quantities $< 0$ are recorded as returns/cancellations and excluded from baseline demand training to prevent negative target distortion.
- **Non-Product Codes:** Administrative entries such as `POST` (Postage), `M` (Manual), `D` (Discount), `BANK CHARGES`, and `TEST` are scrubbed.
- **Price Integrity:** Zero or negative unit prices are dropped (often internal adjustments or gifts).

---

## 3. Table: Aggregated Demand Time-Series (`demand_timeseries`)

Regularized panel time-series aggregated at the product-period grain (`product_week`), forming the direct input to demand forecasting models.

| Column Name | Data Type | Nullable | Computation / Source | Semantic Description |
| :--- | :--- | :--- | :--- | :--- |
| `product_id` | `string` | No | `product_id` | Namespaced canonical product identifier. |
| `period_start` | `timestamp[ns]` | No | Truncated to Monday | Start timestamp of the aggregation period (Monday 00:00:00 UTC). |
| `units_sold` | `float64` | No | $\sum \text{units\_sold}$ | Primary target variable $Q_{i,t}$: Total units demanded in the period. Zero-filled. |
| `mean_unit_price` | `float64` | No | $\frac{\sum (\text{units} \cdot \text{price})}{\sum \text{units}}$ | Weighted average observed transaction unit price. Forward-filled for zero-demand weeks. |
| `transaction_count`| `int64` | No | Count of transactions | Number of discrete sales orders recorded for this product in period $t$. |

### Regularization Policy
- **Calendar Grid:** Continuous weekly frequency (`W-MON`). Every active product is aligned to an uninterrupted chronological grid from its first observed week to the dataset boundary.
- **Zero-Imputation:** Weeks where zero units were ordered receive $Q_{i,t} = 0$ and `transaction_count` = 0.
- **Price Continuity:** If $Q_{i,t} = 0$, `mean_unit_price` is forward-filled from the most recent active selling price, avoiding artificial price drops.

---

## 4. Table: Canonical Product Catalog (`product_catalog`)

Master dimension table representing unique catalog SKUs.

| Column Name | Data Type | Nullable | Source Column | Semantic Description |
| :--- | :--- | :--- | :--- | :--- |
| `product_id` | `string` | No | `uci_<StockCode>` | Namespaced canonical SKU key. Primary key. |
| `product_name` | `string` | No | `Description` | Canonical product title / description (modal string). |
| `category` | `string` | No | Derived / Default | Product taxonomy category (e.g. `"General Merchandise"`). |
| `first_observed_at`| `timestamp[ns]` | No | Minimum `InvoiceDate` | Timestamp of first observed transaction. |
| `last_observed_at` | `timestamp[ns]` | No | Maximum `InvoiceDate` | Timestamp of most recent transaction. |
| `is_active` | `bool` | No | Derived | Boolean flag indicating whether product has sales in the trailing 90 days. |

---

## 5. Storage Formats & Locations

- **Canonical Observations:** `data/processed/sales_observations.parquet` (Snappy compression, dictionary encoding).
- **Aggregated Series:** `data/processed/demand_timeseries.parquet`.
- **Product Catalog:** `data/processed/product_catalog.parquet`.
- **Manifest Tracking:** Each file's SHA-256 hash, row count, byte size, and column list are recorded in `data/manifests/derived_data_manifest.json`.
