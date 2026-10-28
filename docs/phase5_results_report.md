# MarketLens AI — Phase 5 Feature Ablation & Scientific Evaluation Report

**Document Identifier:** `docs/phase5_results_report.md`  
**Phase:** Phase 5 — Hybrid ML Integration, Feature Ablation, and Evidence-Based Evaluation  
**Status:** Canonical Results Report  
**Date:** 2026-10-29  
**Run ID:** `ablation_phase5_hybrid_feature_ablation_20261029_003319`  

---

## 1. Executive Summary

Phase 5 addresses the core empirical research question of MarketLens AI:
> *Do validated customer-review sentiment and competitor-price signals improve demand forecasts, and do any measured forecasting improvements translate into more credible pricing recommendations?*

In strict adherence to Project Principle 1 (*No fabricated market data*) and Principle 2 (*Keep synthetic data separate*), this study was executed against the primary acquired transaction dataset (`uci_online_retail_ii`).

### Key Findings
1. **Real-World Empirical Evaluation:**
   * **E0 (Baseline):** Conventional historical sales, price, and calendar features were evaluated on 450 out-of-sample test weeks across 50 top giftware/homeware products, yielding $\text{MAE} = 276.73$, $\text{RMSE} = 348.53$, $\text{WAPE} = 1.584$, $\text{MASE} = 4.53$, and $R^2 = -0.233$.
   * **E1 (Reviews), E2 (Competitors), E3 (Both):** Rigorously designated **`NOT_RUN (MISSING_REAL_DATA)`** in the real-world benchmark table because the UCI Online Retail II dataset contains transactional records only, with no customer reviews or competitor price feeds.
2. **Software Pipeline Verification:**
   * The complete end-to-end integration architecture—including time-aligned feature joins, lookback window enforcement, anti-leakage filtering ($t_{\text{obs}} \le t_{\text{origin}}$), model training, metric evaluation, signed delta reporting, and Phase 3 constrained pricing optimization—was verified via 21 dedicated Phase 5 automated tests and 151 total passing repository tests.
3. **Pricing Impact Analysis:**
   * Integrating the baseline demand model into the Phase 3 `PricingOptimizer` generated revenue-optimal candidate recommendations within the $[-25\%, +25\%]$ movement boundary without violating business constraints or triggering out-of-support extrapolation warnings.

---

## 2. Research Protocol & Chronological Split Design

* **Dataset:** UCI Online Retail II (`data/processed/demand_timeseries.parquet`, 779,495 transaction records aggregated to weekly grain).
* **Entity Grain:** Product-week (`W-MON`, calendar-regularized with zero-demand imputation).
* **Forecast Horizon:** $h = 1$ week ahead.
* **Forecast Origin:** Monday 00:00:00 UTC at the beginning of each period.
* **Chronological Holdout Split (No Lookahead Shuffle):**
  * **Train Set:** 2,000 product-week periods ($2009\text{-}11\text{-}30 \to 2010\text{-}08\text{-}30$, 70%).
  * **Validation Set:** 450 product-week periods ($2010\text{-}09\text{-}06 \to 2010\text{-}11\text{-}01$, 15%).
  * **Held-Out Test Set:** 450 product-week periods ($2010\text{-}11\text{-}08 \to 2011\text{-}01\text{-}03$, 15%).
* **Shared Cohort:** All evaluations were conducted on the identical set of 450 held-out test rows across 50 top-selling products.

---

## 3. Four-Way Feature-Ablation Benchmark Results

The table below presents the official held-out test set evaluation across the four logical experiment variants on real historical data:

| Variant | Variant Name | Execution Status | Feature Count | Test Rows | MAE | RMSE | WAPE | MASE | $R^2$ | $\Delta\text{MAE}$ | $\%\Delta\text{MAE}$ | Scientific Evaluation Notes |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **E0** | **Baseline** | **COMPLETED** | 14 | 450 | **276.73** | **348.53** | **1.584** | **4.53** | **-0.233** | *Baseline* | *Baseline* | Evaluated on canonical sales lags, price lags, and calendar features. |
| **E1** | **Baseline + Reviews** | **NOT_RUN** | 14 | 0 | — | — | — | — | — | — | — | *Not run on real data: UCI Online Retail II contains no review text.* |
| **E2** | **Baseline + Competitors** | **NOT_RUN** | 14 | 0 | — | — | — | — | — | — | — | *Not run on real data: UCI Online Retail II contains no competitor prices.* |
| **E3** | **Baseline + Both** | **NOT_RUN** | 14 | 0 | — | — | — | — | — | — | — | *Not run on real data: missing real review text and competitor price feeds.* |

*Sign convention: For loss metrics (MAE, RMSE, WAPE, MASE), negative $\Delta$ represents improvement.*

---

## 4. Anti-Leakage & Temporal Verification Evidence

Strict temporal isolation was mathematically verified through the automated test suite:
1. **Origin Cutoff Test (`test_anti_leakage_future_signals_purged`):** Verified that external signals timestamped even 1 second after Monday 00:00:00 UTC are completely purged from the feature record.
2. **Lookback Boundary Test (`test_build_market_signal_features_within_lookback`):** Verified that reviews older than 30 days and competitor observations older than 7 days are excluded from trailing rolling windows.
3. **Adversarial Perturbation Proof (`test_adversarial_temporal_integrity_proof`):** Verified that injecting an adversarial future negative review (48 hours ahead) and a 75% competitor price slash (24 hours ahead) results in zero perturbation of historical features.
4. **Missingness Indicator Test (`test_missing_market_signals_indicator_flags`):** Verified that missing external market data does not default to zero sentiment or zero competitor price; explicit indicator flags (`review_signal_missing = 1`, `competitor_signal_missing = 1`) are emitted.

---

## 5. Pricing Impact & Optimizer Coupling

The Phase 3 `PricingOptimizer` was coupled to the primary random forest demand forecaster:
* **Evaluated Product:** SKU `10002` (Giftware item, base volume-weighted selling price: £0.85).
* **Evaluated Candidate Grid:** Discrete increments across $[£0.64, £1.06]$ ($\pm 25\%$).
* **Optimizer Outcome:**
  * Status: `OPTIMAL_PROPOSAL`.
  * Recommended Price: £0.85 (equal to current price, reflecting low predicted demand elasticity in this discrete interval).
  * Feasibility: 100% of candidate prices satisfied gross margin and price movement constraints.
  * Extrapolation Guard: Candidate prices remained within the historical training support bounds $[£0.42, £1.70]$.

---

## 6. Limitations & Threats to Validity

1. **Dataset Breadth:** The primary dataset represents UK B2B wholesale giftware. Generalizing demand elasticity patterns to B2C consumer electronics or fast-moving consumer goods requires testing on additional datasets.
2. **Missing Real Market Feeds:** Real-world validation of Hypotheses $H_1$, $H_2$, and $H_3$ remains blocked until an authorized secondary dataset with natural language customer reviews (e.g., Olist or Amazon giftware) and competitor pricing feeds is integrated.
3. **Correlational Demand Limitations:** The Random Forest demand model captures observational historical correlations. It is not an unconfounded causal model; pricing recommendations should remain strictly human-supervised decision support.

---

## 7. Artifact Lineage & Persistence References

All Phase 5 artifacts were serialized atomically to `artifacts/phase5/`:
* **Metrics Table (CSV):** [`artifacts/phase5/ablation_metrics.csv`](file:///d:/Professional%20Projects/Agentic_Dynammic_Intelligence_Platform/artifacts/phase5/ablation_metrics.csv)
* **Metrics Table (JSON):** [`artifacts/phase5/ablation_metrics.json`](file:///d:/Professional%20Projects/Agentic_Dynammic_Intelligence_Platform/artifacts/phase5/ablation_metrics.json)
* **Run Manifest (JSON):** [`artifacts/phase5/ablation_run_manifest.json`](file:///d:/Professional%20Projects/Agentic_Dynammic_Intelligence_Platform/artifacts/phase5/ablation_run_manifest.json)
* **Predictions (Parquet):** [`artifacts/phase5/ablation_predictions.parquet`](file:///d:/Professional%20Projects/Agentic_Dynammic_Intelligence_Platform/artifacts/phase5/ablation_predictions.parquet)
