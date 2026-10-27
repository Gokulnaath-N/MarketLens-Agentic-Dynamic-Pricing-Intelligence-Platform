# Data Dictionary — UCI Online Retail II

This data dictionary documents the exact columns, verified data types, statistical distributions, and semantic interpretations for the acquired `data/raw/uci_online_retail_ii/online_retail_II.xlsx` file.

---

## 1. Schema Overview

- **Source File:** `data/raw/uci_online_retail_ii/online_retail_II.xlsx`
- **Granularity:** Transaction line-item (single SKU per invoice event)
- **Time Range (100k sample):** `2009-12-01 07:45:00` to `2010-02-23 10:50:00` (Full file spans 2009 to 2011)
- **Currency:** British Pounds Sterling (GBP, £)

| Column Name | Inferred Type | Missing Count | Missing % | Distinct Count (Sample) | Semantic Role |
| :--- | :--- | :-: | :-: | :-: | :--- |
| **`Invoice`** | `object` / `string` | 0 | 0.00% | 5,524 | Primary Transaction Identifier |
| **`StockCode`** | `object` / `string` | 0 | 0.00% | 3,752 | Product / SKU Identifier |
| **`Description`** | `object` / `string` | 870 | 0.87% | 3,426 | Product Name / Text Title |
| **`Quantity`** | `int64` | 0 | 0.00% | 372 | Units Sold (Target Candidate) |
| **`InvoiceDate`** | `datetime64[ns]` | 0 | 0.00% | 4,779 | Event Timestamp (Time Index) |
| **`Price`** | `float64` | 0 | 0.00% | 612 | Observed Unit Selling Price |
| **`Customer ID`** | `float64` / `int` | 26,451 | 26.45% | 1,757 | Customer Identifier |
| **`Country`** | `object` / `string` | 0 | 0.00% | 32 | Customer Residence / Market |

---

## 2. Detailed Field Definitions & Quality Notes

### `Invoice`
- **Description:** A 6-digit integral number uniquely assigned to each transaction.
- **Cancellation Flag:** If this code starts with letter `'C'`, it indicates an official transaction cancellation or return.
- **Handling Rule for Phase 2:** Transactions with invoice codes starting with `'C'` must be filtered or matched against original purchases to avoid distorting baseline sales demand.

### `StockCode`
- **Description:** A 5-digit integral or alphanumeric string uniquely assigned to each distinct product.
- **Examples:** `'85048'`, `'79323P'`, `'POST'`, `'M'` (Manual), `'D'` (Discount).
- **Handling Rule for Phase 2:** Non-product administrative codes (`'POST'`, `'M'`, `'BANK CHARGES'`) should be separated from retail SKU demand.

### `Description`
- **Description:** Product title in plain English text.
- **Missingness:** Missing in ~0.87% of transaction lines (often corresponding to damaged inventory or manual adjustments).

### `Quantity`
- **Description:** The quantities of each product per transaction.
- **Distribution:** Median = 3.0 units, Minimum = -4,200 units (return/cancellation), Maximum = 19,152 units.
- **Quality Alert:** Negative quantities correspond to returned merchandise. In Phase 2, aggregate demand will sum positive net units at the chosen time grain.

### `InvoiceDate`
- **Description:** The day and time when each transaction was generated.
- **Format:** `YYYY-MM-DD HH:MM:SS`.
- **Handling Rule for Phase 2:** Serves as the temporal axis for chronological train/validation/test splits and rolling lag feature creation.

### `Price`
- **Description:** Unit price of the product in Sterling (£).
- **Distribution:** Non-negative; zero prices occur in promotional giveaways, administrative corrections, or unpriced samples.

### `Customer ID`
- **Description:** 5-digit integral number uniquely assigned to each registered customer.
- **Missingness:** Missing in ~26.45% of records (representing guest checkouts without an account).

### `Country`
- **Description:** The name of the country where each customer resides. The dominant market is the United Kingdom (>90% of transactions).

---

## 3. Unsupported Fields in Raw Data

To maintain scientific integrity, the following signals are explicitly documented as **absent** from the raw UCI Online Retail II dataset:
- `competitor_price`: No competitor observations are provided.
- `customer_reviews`: No customer review text or satisfaction ratings are recorded.
- `unit_cost`: No wholesale unit cost of goods sold is supplied.
- `inventory_level`: No stock availability or stockout timestamps are reported.
