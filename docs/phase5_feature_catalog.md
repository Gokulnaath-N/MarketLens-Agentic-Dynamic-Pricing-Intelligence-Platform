# MarketLens AI — Phase 5 Canonical Feature Catalog

**Document Identifier:** `docs/phase5_feature_catalog.md`  
**Phase:** Phase 5 — Hybrid ML Integration, Feature Ablation, and Evidence-Based Evaluation  
**Status:** Canonical  
**Date:** 2026-10-29  

---

## 1. Overview and Architecture

This catalog defines all features utilized across the four feature-ablation experiment variants (E0 Baseline, E1 Reviews, E2 Competitor Intelligence, E3 Both).

All features adhere to strict anti-leakage temporal availability constraints: for a forecast origin at Monday $t_{\text{origin}}$, all raw inputs must have observation timestamps $t_{\text{obs}} \le t_{\text{origin}}$.

---

## 2. Feature Group 0: Conventional Baseline Features (E0)

| Feature Name | Type | Unit | Lookback Window | Calculation & Definition | Missing Value Policy | Permitted Variants |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `target_lag_1` | Float | Units | $t-1$ | Units sold at prior week $t-1$. | Impute 0.0 (zero historical sales). | E0, E1, E2, E3 |
| `target_lag_2` | Float | Units | $t-2$ | Units sold at 2 weeks prior $t-2$. | Impute 0.0. | E0, E1, E2, E3 |
| `target_lag_4` | Float | Units | $t-4$ | Units sold at 4 weeks prior $t-4$. | Impute 0.0. | E0, E1, E2, E3 |
| `price_lag_1` | Float | GBP | $t-1$ | Volume-weighted average unit price at week $t-1$. | Forward-fill product catalog price or median price. | E0, E1, E2, E3 |
| `rolling_mean_4` | Float | Units | $[t-4, t-1]$ | 4-week trailing rolling mean of units sold. | Impute with available periods; fill 0.0. | E0, E1, E2, E3 |
| `rolling_std_4` | Float | Units | $[t-4, t-1]$ | 4-week trailing rolling standard deviation of units. | Impute 0.0. | E0, E1, E2, E3 |
| `rolling_mean_8` | Float | Units | $[t-8, t-1]$ | 8-week trailing rolling mean of units sold. | Impute with available periods; fill 0.0. | E0, E1, E2, E3 |
| `rolling_std_8` | Float | Units | $[t-8, t-1]$ | 8-week trailing rolling standard deviation of units. | Impute 0.0. | E0, E1, E2, E3 |
| `price_rolling_mean_4`| Float | GBP | $[t-4, t-1]$ | 4-week trailing rolling mean of unit selling price. | Forward-fill catalog price. | E0, E1, E2, E3 |
| `cal_month` | Int | Month | Period $t$ | Calendar month of forecast target period ($1–12$). | Exact deterministic calendar integer. | E0, E1, E2, E3 |
| `cal_quarter` | Int | Quarter | Period $t$ | Calendar quarter ($1–4$). | Exact deterministic calendar integer. | E0, E1, E2, E3 |
| `cal_week_of_year` | Int | Week | Period $t$ | ISO week number ($1–53$). | Exact deterministic calendar integer. | E0, E1, E2, E3 |
| `sin_month` | Float | Radians | Period $t$ | $\sin(2\pi \cdot \text{month} / 12)$. | Cyclical transformation. | E0, E1, E2, E3 |
| `cos_month` | Float | Radians | Period $t$ | $\cos(2\pi \cdot \text{month} / 12)$. | Cyclical transformation. | E0, E1, E2, E3 |

---

## 3. Feature Group 1: Customer Review & Perception Signals (E1, E3)

Derived from validated `ReviewInsightOutput` records timestamped $t_{\text{review}} \le t_{\text{origin}}$.

| Feature Name | Type | Range / Unit | Lookback Window | Calculation & Definition | Missing Value Policy | Permitted Variants |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `review_count_30d` | Int | $\ge 0$ | 30 days | Total raw customer reviews submitted in trailing 30 days. | 0 if no reviews present. | E1, E3 |
| `usable_review_count_30d` | Int | $\ge 0$ | 30 days | Non-failed reviews with unambiguous sentiment label. | 0 if no reviews present. | E1, E3 |
| `mean_sentiment_30d` | Float | $[-1.0, 1.0]$ | 30 days | Average normalized sentiment score among usable reviews. | Null / NaN; imputed with neutral 0.0 in ML model + flag. | E1, E3 |
| `positive_review_ratio_30d`| Float | $[0.0, 1.0]$ | 30 days | $\frac{\text{Positive Reviews}}{\text{Usable Reviews}}$ in trailing 30 days. | Null / NaN; imputed 0.0. | E1, E3 |
| `negative_review_ratio_30d`| Float | $[0.0, 1.0]$ | 30 days | $\frac{\text{Negative Reviews}}{\text{Usable Reviews}}$ in trailing 30 days. | Null / NaN; imputed 0.0. | E1, E3 |
| `aspect_quality_mentions_30d`| Int | $\ge 0$ | 30 days | Count of reviews citing `product_quality` aspect. | 0 if no mentions. | E1, E3 |
| `aspect_value_mentions_30d` | Int | $\ge 0$ | 30 days | Count of reviews citing `value_for_money` aspect. | 0 if no mentions. | E1, E3 |
| `review_signal_missing` | Int | $\{0, 1\}$ | Point in time | Binary indicator: 1 if review signal is absent or sample $< 5$. | 1 if no reviews; 0 if available. | E1, E3 |

---

## 4. Feature Group 2: Competitor Price & Dynamics Signals (E2, E3)

Derived from validated `CompetitorObservation` and `CompetitorChangeEvent` records timestamped $t_{\text{obs}} \le t_{\text{origin}}$.

| Feature Name | Type | Unit | Lookback Window | Calculation & Definition | Missing Value Policy | Permitted Variants |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `competitor_count_7d` | Int | $\ge 0$ | 7 days | Number of unique competitors observing price in trailing 7 days. | 0 if no observations. | E2, E3 |
| `min_competitor_price_7d`| Float | Currency | 7 days | Lowest observed competitor price for the focal SKU. | Null / NaN; imputed with own price + flag. | E2, E3 |
| `mean_competitor_price_7d`| Float | Currency | 7 days | Average observed competitor price across active merchants. | Null / NaN; imputed with own price. | E2, E3 |
| `competitor_price_gap_pct`| Float | % | 7 days | $\frac{P_{\text{own}} - \min(P_{\text{comp}})}{\min(P_{\text{comp}})} \times 100\%$. Positive = own price higher. | Null / NaN; imputed 0.0% + flag. | E2, E3 |
| `latest_competitor_price_change_pct` | Float | % | 7 days | Percentage change of most recent competitor price event. | Null / NaN; imputed 0.0%. | E2, E3 |
| `competitor_price_drop_flag` | Int | $\{0, 1\}$ | 7 days | Binary indicator: 1 if any competitor dropped price $\ge 5\%$ in 7d. | 0 if no drop or no data. | E2, E3 |
| `competitor_signal_missing` | Int | $\{0, 1\}$ | Point in time | Binary indicator: 1 if no valid competitor observations exist. | 1 if missing; 0 if observed. | E2, E3 |

---

## 5. Mandatory Anti-Leakage Integration Rules

1. **Strict Origin Cutoff:**
   Features for weekly period $t$ (starting Monday 00:00 UTC) must never include reviews or competitor observations timestamped after Monday 00:00 UTC.
2. **Missingness Preservation:**
   Missing signals must be represented via explicit missingness indicator columns (`review_signal_missing`, `competitor_signal_missing`). ML models must not mistake the absence of competitor data for equal competitor pricing.
3. **No Target Leakage in Price Gaps:**
   When calculating `competitor_price_gap_pct`, the focal product price $P_{\text{own}}$ must be the decision-origin price (`price_lag_1` or catalog price), never the future volume-weighted price of period $t$.
