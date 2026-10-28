# MarketLens AI — Phase 3 Input & Environment Audit
Constrained Pricing Optimization Engine Input Verification

**Document Version:** 1.0.0  
**Audit Date:** 2026-10-28  
**Author:** Principal Engineer & Applied Data Scientist  
**Status:** COMPLETE & VERIFIED  

---

## 1. Executive Summary

This audit assesses the state of the repository, data assets, and model interfaces from Phase 0–2 to establish exact prerequisites and constraints before implementing the Phase 3 **Constrained Pricing Optimization Engine**.

In accordance with MarketLens AI principles (Principle 2: *No fabricated data*, Principle 6: *No false causal claims*, Principle 7: *Guard against extrapolation*, and Principle 8: *Fail closed*), all findings reflect observed repository facts rather than assumptions.

---

## 2. Audit Findings Against Required Questions

### Q1. Which actual Phase 2 dataset and model artifacts exist?
- **Raw Transaction Data:** `data/raw/online_retail_ii.xlsx` (1,067,373 rows across 2 sheets, verified SHA-256 in `data/manifests/dataset_manifest.json`, CC BY 4.0 license).
- **Processed Datasets (Parquet):**
  - `data/processed/sales_observations.parquet` (95,951 cleaned sales line items).
  - `data/processed/demand_timeseries.parquet` (2,900 product-week records across 50 top SKUs, weekly Monday grain `W-MON`).
- **Derived Lineage Manifest:** `data/manifests/derived_data_manifest.json` (records exact row counts, exclusion audit, and SHA-256 hashes).
- **Evaluation Artifacts:**
  - `artifacts/model_comparison.json` & `artifacts/model_comparison.csv` (recording MAE, RMSE, WAPE, MASE, $R^2$ on 450 held-out test rows).
  - `artifacts/test_predictions.parquet` (out-of-sample predictions).

### Q2. Does the demand model accept candidate price as an input?
- **Finding:** The four Phase 2 baseline models (`NaiveLastObservedForecaster`, `MovingAverageForecaster`, `RidgeRegressionForecaster`, and `RandomForestDemandForecaster`) are trained on autoregressive historical features:
  - Lags: `target_lag_1`, `target_lag_2`, `target_lag_4`
  - Historical Price: `price_lag_1` (historical price at $t-1$), `price_rolling_mean_4`, `price_rolling_mean_8`
  - Calendar: `cal_month`, `cal_quarter`, `cal_week_of_year`, `sin_month`, `cos_month`.
- **Critical Observation:** None of the Phase 2 baseline models were trained on contemporaneous candidate price ($P_{t+h}$ where $h=1$) because in pure observational sales logs, future candidate price was not treated as a decision intervention variable.
- **Consequence:** A model that depends solely on historical lags is **price-invariant** at decision time ($\frac{\partial \hat{Q}}{\partial p} = 0$). If candidate price $p$ is varied, $\hat{Q}(p)$ remains identical, causing revenue $p \cdot \hat{Q}$ to trivially peak at the upper price bound $p_{\max}$.
- **Resolution:** The pricing optimizer must implement an explicit **Pricing Validity Gate**:
  1. Inspect whether the model interface explicitly supports candidate-price response.
  2. For price-invariant forecasters, refuse to treat predictions as an empirical price-response curve and emit a strict non-actionable status or explicit validation warning.
  3. Provide a typed `DemandPredictorProtocol` and a price-responsive scenario adapter (e.g. constant elasticity $\hat{Q}(p) = \hat{Q}_{\text{base}} \cdot (p / p_0)^\epsilon$) to evaluate scenario pricing while preserving pure baseline model integrity.

### Q3. How can candidate price be injected without changing unrelated features?
- A dedicated scenario builder (`src/marketlens/pricing/scenario.py`) takes fixed product/time context ($\mathbf{x}_{\text{fixed}}$) containing target lags, rolling means, and calendar signals.
- When generating candidate scenarios for price $p$, only the price feature(s) are modulated. Unrelated features (historical sales, seasonality) remain frozen. No future test outcomes or lookahead data are injected.

### Q4. Does a valid unit cost exist, and what is its provenance?
- **Finding:** In UCI Online Retail II, **NO wholesale unit cost (COGS) exists**.
- **Provenance Verification:** Phase 1 `DATA_DICTIONARY.md` and Phase 2 `dataset_limitations.md` explicitly declare that only retail sales transaction price is present.
- **Policy:**
  - For `objective="revenue"`, unit cost is optional.
  - For `objective="profit"`, a validated `unit_cost` $> 0$ **must be provided in the optimization request**.
  - If unit cost is missing or invalid ($\le 0$), the optimizer **fails closed** with an actionable `InfeasibleOptimizationError` or `MissingCostError`.
  - The engine will **never** invent or hallucinate default unit costs. If a synthetic test fixture supplies cost, it is explicitly flagged `is_synthetic=True`.

### Q5. What price bounds and constraints are configured versus missing?
- **Configured in `configs/pricing.yaml`:**
  - `default_objective`: `"revenue"`
  - `min_margin_percentage`: `0.15` (15% margin floor)
  - `max_price_movement_percentage`: `0.20` (max 20% price adjustment from current price)
  - `enforce_non_negative_demand`: `true`
  - `warn_on_unsupported_price`: `true`
  - `require_human_approval`: `true`
  - `auto_reprice_enabled`: `false`
- **Missing / Extended in Phase 3:**
  - Decimal-safe candidate grid generation parameters (`price_step`, `max_candidates`).
  - Extrapolation policy configuration (`reject` vs `warn`).
  - Deterministic tie-breaking rules (highest objective $\to$ closest to current price $\to$ lowest price).
  - Competitor relative premium policy constraints (`max_competitor_price_premium_pct`).

### Q6. What real data can support optimization, and what remains unavailable?
- **Available Real Data:**
  - Real transaction prices and sales volumes in British Pounds (`GBP`).
  - Product-level observed price distributions $[\min(P_i), \max(P_i)]$ for historical support boundaries.
  - Weekly demand seasonality and base sales momentum.
- **Unavailable Data:**
  - Competitor price observations (none in UCI Online Retail II).
  - Customer review sentiment (none in UCI Online Retail II).
  - Wholesale product unit costs (COGS).

### Q7. Any blockers that prevent a defensible recommendation?
- **Primary Blocker:** Pure observational regression models from Phase 2 cannot be claimed as causal price-elasticity estimators without making false causal claims (KB Principle 6 & Section 12.4).
- **Engine Solution:**
  1. Implement complete, deterministic, decimal-safe candidate generation, constraint checking, and objective calculations.
  2. Implement an explicit Model Support and Extrapolation checker using training support $[\min(P_{\text{train}}), \max(P_{\text{train}})]$.
  3. Implement strict human review governance (`human_approval_required = True`).
  4. Implement clear explanation generation detailing active constraints, objective values, and caveats.
  5. Refuse to claim causal optimality.

---

## 3. Implementation Roadmap for Phase 3

Based on these audit conclusions, Phase 3 will construct:
1. `src/marketlens/pricing/schemas.py`: Pydantic input/output schemas with full bounds validation.
2. `src/marketlens/pricing/candidate_generation.py`: Decimal-safe, bounded, deduplicated price grid generator.
3. `src/marketlens/pricing/constraints.py`: Independent validators for margin floor, price movement, competitor rules, and bounds.
4. `src/marketlens/pricing/objectives.py`: Revenue, profit, and gross margin calculations with zero-division safety.
5. `src/marketlens/pricing/scenario.py`: Feature injection and demand predictor protocol.
6. `src/marketlens/pricing/optimizer.py`: Master deterministic optimization loop with support checking and tie-breaking.
7. `src/marketlens/pricing/explanation.py`: Deterministic, evidence-based human-review explanation generator.
8. Comprehensive unit and integration test suite in `tests/unit/` verifying all edge cases.
