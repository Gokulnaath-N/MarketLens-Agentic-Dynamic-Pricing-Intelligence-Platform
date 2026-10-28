# MarketLens AI — Phase 5 Scientific Experiment Protocol

**Document Identifier:** `docs/phase5_experiment_protocol.md`  
**Phase:** Phase 5 — Hybrid ML Integration, Feature Ablation, and Evidence-Based Evaluation  
**Status:** Approved Protocol  
**Date:** 2026-10-29  

---

## 1. Scientific & Business Objectives

### 1.1 Central Research Question
> **RQ:** *Do validated customer-review sentiment and competitor-price signals improve demand forecast accuracy over conventional historical sales and price features, and does this improvement translate into more credible constrained pricing recommendations?*

### 1.2 Core Hypotheses
* **$H_0$ (Null Hypothesis):** External qualitative review sentiment and competitor price movements provide zero statistically or operationally meaningful improvement in forecast error ($\Delta\text{MAE} \ge 0, \Delta\text{WAPE} \ge 0$) compared to an autoregressive temporal baseline.
* **$H_1$ (Review Hypothesis):** Timely customer review sentiment and aspect-level complaint ratios improve forecast accuracy during demand shifts driven by perceived quality changes.
* **$H_2$ (Competitor Hypothesis):** Competitor price gaps and recent price change events improve demand elasticity estimates, reducing forecast bias when competitors adjust prices.
* **$H_3$ (Joint Hypothesis):** Unifying historical transactions, review sentiment, and competitor dynamics yields the lowest overall prediction error and minimizes out-of-support pricing extrapolations.

---

## 2. Target Definition and Temporal Granularity

* **Target Variable:** $y_{i,t} = \text{units\_sold}_{i,t}$, representing total quantity sold for product $i$ during weekly period $t$.
* **Time Grain:** Product-week, anchored to continuous Monday 00:00:00 UTC periods (`W-MON`).
* **Forecast Horizon:** $h = 1$ week ahead.
* **Forecast Origin ($t_{\text{origin}}$):** Monday 00:00:00 UTC at the start of period $t$. The forecast predicts sales spanning $[t, t + 7\text{ days})$.
* **Availability Constraint:** All features for prediction at $t_{\text{origin}}$ must be derived strictly from data timestamped $\le t_{\text{origin}}$.

---

## 3. Four-Way Feature-Ablation Matrix

To isolate the marginal value of each intelligence signal group, the evaluation protocol establishes four strictly controlled experiment variants:

| Variant | Variant Name | Feature Groups Included | Real Data Execution Status |
| :---: | :--- | :--- | :--- |
| **E0** | **Baseline** | Historical sales lags, rolling volume/std, price lags, calendar indicators. | **RUNNABLE** (Evaluated on UCI dataset) |
| **E1** | **Baseline + Reviews** | E0 features + review sentiment score, review volume, aspect complaint/praise counts. | **NOT_RUN** (Missing real review text in UCI) |
| **E2** | **Baseline + Competitors** | E0 features + min/mean competitor price, competitor price gap, recent price drop flag. | **NOT_RUN** (Missing real competitor feeds in UCI) |
| **E3** | **Baseline + Both** | E0 features + all Review and Competitor signals (E1 + E2). | **NOT_RUN** (Missing both real feeds in UCI) |

*Note: For software verification, an isolated synthetic test suite evaluates E0–E3 end-to-end to verify pipeline correctness without contaminating real-world scientific results.*

---

## 4. Modeling Strategy & Evaluation Setup

### 4.1 Model Families
All feature variants are evaluated across the identical model suite established in Phase 2:
1. `naive_last_observed`: Baseline carrying forward target at $t-1$.
2. `moving_average_4w`: Baseline averaging target over previous 4 weeks.
3. `ridge_regression`: Regularized linear model with $\alpha = 10.0$.
4. `random_forest`: Non-linear ensemble (`n_estimators=100`, `max_depth=8`, `random_state=42`).

### 4.2 Data Partitioning Protocol
Strict chronological holdout partitioning (no random shuffle):
* **Training Set:** First 70% of chronological weeks ($t_0 \to t_{\text{train}}$).
* **Validation Set:** Next 15% of chronological weeks ($t_{\text{train}} \to t_{\text{val}}$).
* **Test Set:** Final 15% of chronological weeks ($t_{\text{val}} \to t_{\text{test}}$).

All preprocessing, encoders, and scalers are fitted **strictly on the training partition** and applied out-of-sample to validation and test sets.

---

## 5. Evaluation Metrics and Signed Deltas

Forecast quality is evaluated using zero-safe metrics defined in Phase 2:

1. **Mean Absolute Error (MAE):**
   $$\text{MAE} = \frac{1}{N} \sum_{k=1}^N |y_k - \hat{y}_k|$$
2. **Root Mean Squared Error (RMSE):**
   $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{k=1}^N (y_k - \hat{y}_k)^2}$$
3. **Weighted Absolute Percentage Error (WAPE):**
   $$\text{WAPE} = \frac{\sum_{k=1}^N |y_k - \hat{y}_k|}{\sum_{k=1}^N y_k} \quad (\text{valid only when } \sum y_k > 0)$$
4. **Mean Absolute Scaled Error (MASE):**
   $$\text{MASE} = \frac{\text{MAE}}{\frac{1}{M-1} \sum_{j=2}^M |y_j - y_{j-1}|_{\text{train}}}$$
5. **Coefficient of Determination ($R^2$):**
   $$R^2 = 1 - \frac{\sum (y_k - \hat{y}_k)^2}{\sum (y_k - \bar{y})^2}$$

### 5.1 Delta Reporting Convention
All performance changes are reported relative to the E0 Baseline:
$$\Delta\text{Metric} = \text{Metric}_{\text{Variant}} - \text{Metric}_{\text{E0}}$$
$$\%\Delta\text{Metric} = \frac{\text{Metric}_{\text{Variant}} - \text{Metric}_{\text{E0}}}{\text{Metric}_{\text{E0}}} \times 100\%$$
* For loss metrics (MAE, RMSE, WAPE, MASE): **Negative $\Delta$ indicates improvement**.
* For $R^2$: **Positive $\Delta$ indicates improvement**.

---

## 6. Shared-Cohort & Fair Comparison Rules

1. **Shared Cohort Enforcement:**
   When comparing variants, metrics must be evaluated on the **exact same set of (product, week) rows**. If variant E1 or E2 has missing market signals for some products, the primary comparison must report metrics restricted to the intersection of valid rows across all compared variants.
2. **Missing Market Signals:**
   Missing review or competitor signals must **never** be imputed as zero sentiment (0.0) or zero competitor price (0.00). Numerical models must handle missing signals via explicit missingness indicator flags and zero-neutral imputations with quality status annotations.
3. **Synthetic Data Quarantine:**
   Any synthetic records generated for testing must carry `is_synthetic = True` and be completely isolated from benchmark evaluation artifacts.

---

## 7. Pricing Recommendation Impact Evaluation

To evaluate whether forecast improvements translate into credible pricing actions:
1. Each variant's demand model $\hat{f}(p)$ is integrated into the Phase 3 `ConstrainedPricingOptimizer`.
2. For candidate prices $P = \{p_1, \dots, p_K\}$, the optimizer calculates:
   * Recommended price $p^* = \arg\max_{p \in P_{\text{feasible}}} \text{Objective}(p, \hat{f}(p))$.
   * Feasibility rate and constraint violations (margin floor, price movement limits).
   * Extrapolation warning frequency (prices evaluated outside historical training support).
3. Recommendation changes relative to E0 are recorded and audited for business plausibility.
