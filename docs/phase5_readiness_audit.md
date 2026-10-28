# MarketLens AI — Phase 5 Readiness and Prerequisites Audit

**Document Identifier:** `docs/phase5_readiness_audit.md`  
**Phase:** Phase 5 — Hybrid ML Integration, Feature Ablation, and Evidence-Based Evaluation  
**Status:** Complete  
**Date:** 2026-10-29  

---

## 1. Executive Summary

This readiness audit formally assesses the availability, compatibility, temporal integrity, and scientific viability of the workspace before implementing Phase 5 of MarketLens AI.

Phase 5 addresses the platform's central scientific and business question:
> *Do validated customer-review sentiment and competitor-price signals improve demand forecasts, and do any measured forecasting improvements translate into more credible pricing recommendations?*

In strict adherence to Project Principle 1 (*No fabricated market data*) and Principle 2 (*Keep synthetic data separate*), this audit establishes what real data is empirically present, what baseline pipelines are runnable, and what boundaries must be enforced regarding missing external market feeds.

---

## 2. Repository Components & Artifact Inventory

The workspace was inspected directly via filesystem traversal and automated tests. The following foundational assets were verified:

| Component / Layer | Source Location | Status | Evidence / Validation |
| :--- | :--- | :--- | :--- |
| **Project Foundation & Configs** | `pyproject.toml`, `configs/` (`app.yaml`, `datasets.yaml`, `forecasting.yaml`, `pricing.yaml`, `agents.yaml`) | Verified | YAML loaders, idempotent logging, environment variables active. |
| **Phase 1 Source Provenance** | `data/raw/uci_online_retail_ii/`, `data/manifests/` | Verified | SHA-256 verified streaming download, profile JSON, CC BY 4.0 license attribution. |
| **Phase 2 Canonical Data & Modeling** | `src/marketlens/data/`, `src/marketlens/features/`, `src/marketlens/forecasting/` | Verified | Parquet datasets: `sales_observations.parquet`, `demand_timeseries.parquet` (weekly Monday grain `W-MON`). Chronological holdout (70% train / 15% val / 15% test). |
| **Phase 2 Baseline Results** | `artifacts/model_comparison.csv`, `artifacts/test_predictions.parquet` | Verified | Four baseline models evaluated: Naive ($MAE=169.25$), Moving Average ($MAE=182.93$), Ridge ($MAE=231.54$), Random Forest ($MAE=261.93$). |
| **Phase 3 Pricing Engine** | `src/marketlens/pricing/` | Verified | Decimal-safe candidate grids, revenue/profit objectives, margin floors, price movement limits, and extrapolation guardrails. |
| **Phase 4 Agentic Intelligence** | `src/marketlens/agents/`, `src/marketlens/llm/` | Verified | Pydantic contracts (`MarketSignalAggregate`, `ReviewInsightOutput`, `CompetitorObservation`, `CompetitorChangeEvent`), PII sanitization, prompt injection defense, and offline fallback. |
| **Test Suite Health** | `tests/unit/`, `tests/integration/` | Verified | 140 tests passing with 0 failures across all phases. |

---

## 3. Dataset Assessment & Selected Primary Dataset

1. **Primary Dataset:** `uci_online_retail_ii` (UCI Machine Learning Repository, Giftware & Homeware e-commerce transactions).
2. **Suitability:**
   * High transaction density (779,495 cleaned observation rows across 2009–2011).
   * Verified entity grain: Product-week (`W-MON`).
   * Canonical targets: `units_sold` (weekly aggregated volume) and `mean_unit_price` (volume-weighted average price).
3. **Absence of Natural Language Reviews:**
   * The UCI dataset contains transaction logs only (`Invoice`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `Price`, `Customer ID`, `Country`).
   * It contains **no** customer text reviews, review timestamps, or star ratings.
4. **Absence of Competitor Price Feeds:**
   * Unit prices in UCI represent the retailer's own historical transaction prices.
   * There are **no** third-party merchant competitor price observations.
5. **Phase 5 Data Governance Rule:**
   * **E0 (Baseline)** is fully runnable on real historical transaction data.
   * **E1 (Review)**, **E2 (Competitor)**, and **E3 (Both)** cannot be run against real customer reviews or genuine competitor observations without fabricating data. They must be transparently designated as `NOT_RUN (MISSING_REAL_DATA)` in the real-world scientific results table.
   * To ensure the engineering architecture, feature merger, temporal alignment, and optimizer integration are 100% verified and production-ready, an isolated synthetic test suite (`is_synthetic = True`) is provided. Synthetic fixtures will never be mixed into real scientific evaluation metrics.

---

## 4. Inherited Forecasting & Pricing Primitives

* **Target Variable:** `units_sold` (non-negative integer/float, weekly sum).
* **Forecast Grain:** Product-week (calendar regularized Monday `W-MON` with zero-demand imputation).
* **Forecast Horizon:** $h = 1$ week ahead.
* **Forecast Origin:** Time $t - h$ (Sunday midnight preceding Monday period start).
* **Baseline Features:**
  * Lags: `target_lag_1` ($t-1$), `target_lag_2` ($t-2$), `target_lag_4` ($t-4$).
  * Price: `price_lag_1` ($t-1$), `price_rolling_mean_4`, `price_rolling_mean_8`.
  * Rolling Stats: `rolling_mean_4`, `rolling_std_4`, `rolling_mean_8`, `rolling_std_8`.
  * Calendar: `cal_month`, `cal_quarter`, `cal_week_of_year`, `sin_month`, `cos_month`.
* **Primary Evaluated Model Families:**
  * `naive_last_observed`: Non-parametric heuristic baseline.
  * `moving_average_4w`: Historical smoothing baseline.
  * `ridge_regression`: L2-regularized linear baseline.
  * `random_forest`: Non-linear decision forest.

---

## 5. Temporal Alignment & Anti-Leakage Audit

1. **Forecast Decision Time:**
   For a prediction targeting period $T = [t, t + 7\text{ days})$, the decision is made at forecast origin $t_{\text{origin}} = t$.
2. **Leakage-Safe Cutoff Condition:**
   Any external signal $s$ (review perception or competitor observation) is eligible for inclusion in the feature record for origin $t_{\text{origin}}$ if and only if:
   $$t_{\text{obs}}(s) \le t_{\text{origin}}$$
3. **Lookback Windows:**
   * Review perception window: Trailing 30 days $[t_{\text{origin}} - 30\text{d}, t_{\text{origin}}]$.
   * Competitor price window: Trailing 7 days $[t_{\text{origin}} - 7\text{d}, t_{\text{origin}}]$.
4. **Leakage Verification:**
   All features must pass perturbation tests: altering any record with $t_{\text{obs}} > t_{\text{origin}}$ must cause zero change in the feature vector for $t_{\text{origin}}$.

---

## 6. Audit Conclusion & Execution Strategy

| Variant | Scientific Status on Real UCI Data | Synthetic Smoke/Test Suite Status | Action Plan |
| :--- | :--- | :--- | :--- |
| **E0 (Baseline)** | **Fully Runnable** | Verified | Run full evaluation across train/validation/test splits. |
| **E1 (Review)** | **NOT_RUN** (Missing real reviews) | Fully Verified via Synthetic Pipeline | Implement pipeline, verify with synthetic fixtures, document data gap. |
| **E2 (Competitor)**| **NOT_RUN** (Missing competitor feed)| Fully Verified via Synthetic Pipeline | Implement pipeline, verify with synthetic fixtures, document data gap. |
| **E3 (Both)** | **NOT_RUN** (Missing both feeds) | Fully Verified via Synthetic Pipeline | Implement pipeline, verify with synthetic fixtures, document data gap. |

The workspace is fully prepared for Phase 5 implementation.
