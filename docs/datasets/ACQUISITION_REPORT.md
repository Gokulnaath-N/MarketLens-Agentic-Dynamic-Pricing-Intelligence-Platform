# MarketLens AI — Phase 1 Dataset Acquisition and Profiling Report

- **Date:** 2026-10-27
- **Phase:** Phase 1 (Dataset Discovery, License Review, Bounded Acquisition, Provenance & Profiling)
- **Author:** Senior Data Engineer / Data Governance Agent

---

## 1. Executive Summary

In Phase 1, the dataset discovery, rights review, and bounded streaming acquisition engine was implemented and executed for **MarketLens AI**. 

Four candidate public datasets were evaluated against MarketLens AI's scientific and licensing criteria:
1. **UCI Online Retail II** passed all hard gates, was selected as the primary transaction sales baseline, and was successfully downloaded, integrity-verified, extracted, and profiled.
2. **Olist Brazilian E-Commerce** was evaluated as a candidate for review-sentiment analysis, but was flagged as `BLOCKED_CREDENTIALS` because Kaggle API credentials are not configured in the local environment.
3. **M5 Forecasting Accuracy** was evaluated as a store-forecasting benchmark, but was flagged as `BLOCKED_CREDENTIALS` and size-budget constrained (>500 MB).
4. **Amazon Reviews 2023** was evaluated and deferred as an optional category streaming source.

All downloaded raw artifacts have been stored immutably under `data/raw/uci_online_retail_ii/` and cataloged in `data/manifests/datasets_manifest.json`.

---

## 2. Candidate Evaluation & Hard-Gate Decisions

| Candidate ID | Name | Role | License | Suitability Score | Hard Gate Status | Decision | Decision Rationale |
| :--- | :--- | :--- | :--- | :-: | :-: | :-: | :--- |
| `uci_online_retail_ii` | UCI Online Retail II | Primary Sales Baseline | CC BY 4.0 | 85.0 / 100 | **PASSED** | **SELECTED** | Verified open license, direct public HTTPS download, over 1M real retail transactions with timestamps, prices, and quantities. |
| `olist_brazilian_ecommerce` | Olist Brazilian E-Commerce | Review Benchmark | CC BY-NC-SA 4.0 | 77.0 / 100 | **BLOCKED** | **BLOCKED** | Blocked due to missing Kaggle API credentials in local environment. |
| `m5_forecasting` | M5 Forecasting Accuracy | Forecasting Benchmark | Kaggle Competition Rules | 65.0 / 100 | **BLOCKED** | **BLOCKED** | Requires Kaggle competition rules acceptance and credentials; size exceeds default Phase 1 limit. |
| `amazon_reviews_2023` | Amazon Reviews 2023 | Review NLP Benchmark | Academic Research Terms | 62.0 / 100 | **PASSED** | **OPTIONAL** | Full corpus exceeds 100 GB; deferred for targeted category streaming in Phase 4. |

---

## 3. Physical File Acquisition Audit

The following files were acquired using `BoundedDownloader` with SHA-256 validation:

| Filename | Storage Path | Format | Size (Bytes) | Size (MB) | SHA-256 Hash | Validation |
| :--- | :--- | :---: | :-: | :-: | :--- | :---: |
| `online_retail_ii.zip` | `data/raw/uci_online_retail_ii/online_retail_ii.zip` | ZIP | 45,622,418 | 43.51 MB | `572e36277c2390fbfde10664750731e0a86f55e33470d91919085f0408e67bfb` | Verified |
| `online_retail_II.xlsx` | `data/raw/uci_online_retail_ii/online_retail_II.xlsx` | XLSX | 45,622,278 | 43.51 MB | `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980` | Verified |

- **Source URL:** `https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip`
- **Integrity Checks:** File magic verified (`PK\x03\x04`), safe archive extraction performed without path traversal or expansion anomalies.

---

## 4. Tabular Data Profiling Summary

A read-only profiling scan of the first 100,000 transaction rows of `online_retail_II.xlsx` yielded:
- **Dimensions:** 100,000 rows × 8 columns
- **Date Range:** `2009-12-01 07:45:00` to `2010-02-23 10:50:00`
- **Detected Target Column:** `Quantity` (integer units sold)
- **Detected Price Column:** `Price` (unit selling price in GBP)
- **Detected Time Column:** `InvoiceDate` (datetime timestamp)
- **Detected Product Keys:** `StockCode` (3,752 distinct SKUs), `Invoice` (5,524 distinct invoices)
- **Duplicate Rows in Sample:** 545 duplicate transaction lines (0.55%)

### Identified Data Quality Issues:
1. **Cancellations & Negative Quantities:** Minimum quantity observed is `-4,200.0`. Invoices starting with `'C'` represent return merchandise and require explicit filtering or netting in Phase 2.
2. **Zero Price Observations:** `Price` has a minimum value of `0.0`. These occur in promotional giveaways, samples, or administrative adjustments.
3. **Guest Checkout Nulls:** `Customer ID` has 26,451 missing values (26.45%), indicating guest purchases. Demand modeling at the SKU-day level is unaffected by missing customer IDs.

---

## 5. MarketLens AI Feature Suitability Matrix

| Feature / Subsystem | UCI Online Retail II Support | Implementation Strategy |
| :--- | :---: | :--- |
| **Historical Demand Forecasting** | **Fully Supported** | Aggregation of net sales quantity by `StockCode` and day/week. |
| **Price Elasticity Modeling** | **Supported** | Observed selling `Price` varies across transactions and over time. |
| **Calendar & Lag Features** | **Fully Supported** | `InvoiceDate` provides fine-grained timestamp for day-of-week, month, and lag creation. |
| **Competitor Price Monitoring** | **Not Available in Raw Data** | Raw data contains only own selling prices. In Phase 4, competitor feeds will be integrated via authorized secondary source or clearly tagged simulation. |
| **Customer Review Sentiment** | **Not Available in Raw Data** | Raw data contains product descriptions but no customer reviews. Review NLP benchmarking will use a separate review bundle in Phase 4. |
| **Profit Maximization Objective** | **Constrained / Not Available** | Wholesale unit cost is absent. In Phase 3, optimization will default to the **Revenue** objective; profit will require explicit user-provided cost parameters or simulation labeling. |

---

## 6. Recommendations for Phase 2

1. **Filtering & Netting:** Clean transaction rows by separating cancellations (`Invoice.str.startswith('C')`) and non-product SKU codes (`'POST'`, `'D'`).
2. **Entity Grain Selection:** Profile sparsity across daily vs. weekly aggregations to establish whether `product_day` or `product_week` provides optimal signal-to-noise.
3. **Chronological Splitting:** Maintain strict chronological holdout splits (e.g. 70% train, 15% validation, 15% test) based on `InvoiceDate` to prevent lookahead leakage.
