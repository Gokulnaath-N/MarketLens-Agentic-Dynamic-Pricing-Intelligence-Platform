# MarketLens AI — Pricing Engine Limitations & Governance

**Document Version:** 1.0.0  
**Phase:** Phase 3 (Constrained Pricing Optimization)  
**Status:** Approved & Implemented  
**Date:** 2026-10-28  

---

## 1. Executive Summary & Principles

The MarketLens AI pricing optimization engine is strictly a **decision-support system**. It evaluates discrete candidate prices under configured commercial rules and demand model predictions to provide evidence-based, reviewable proposals for human category managers.

In strict compliance with MarketLens AI principles (Principle 1: *Decision support only*, Principle 6: *No false causal claims*, Principle 7: *Guard against extrapolation*, and Principle 8: *Fail closed*), this document defines the boundaries, known data gaps, and operational limitations of the engine.

---

## 2. Core Methodological & Data Limitations

### 2.1 Observational Correlation vs. Causal Price Elasticity
- **Limitation:** In observational transaction logs (such as the primary dataset, UCI Online Retail II), historical price variations were not generated through controlled randomized trials. Price fluctuations often coincide with seasonal promotions, clearance sales of retiring products, end-of-year holidays, or volume bulk tiers.
- **Consequence:** An empirical regression or tree-based machine learning model fits historical conditional correlations $\mathbb{E}[Q \mid P=p, \mathbf{X}=\mathbf{x}]$, which does **not** equal the causal counterfactual $\mathbb{E}[Q \mid \text{do}(P=p), \mathbf{X}=\mathbf{x}]$.
- **Policy:** The engine explicitly states that its recommendations optimize the objective **only among the evaluated candidate grid under model assumptions**. It strictly forbids claiming that a proposed price will cause a guaranteed demand or revenue uplift.

### 2.2 Price Invariance in Autoregressive Demand Models
- **Limitation:** Pure time-series forecasters (such as naive last-observed or autoregressive lag models) predict future quantities using only prior historical lags ($Q_{t-1}, Q_{t-2}$) and calendar signals.
- **Consequence:** If candidate price $p$ is varied at forecast origin $t$, a price-invariant model produces a constant predicted demand ($\frac{\partial \hat{Q}}{\partial p} = 0$). Evaluating revenue $p \cdot \hat{Q}$ against a flat demand curve would trivially select the highest permitted price bound ($P_{\max}$).
- **Policy:** The engine enforces a **Pricing Validity Gate**:
  - If a demand model does not vary its predictions when candidate prices change, the engine halts immediately and returns status `PRICE_INVARIANT_MODEL`.
  - It refuses to present invariant predictions as valid price-response curves.

### 2.3 Absence of Wholesale Unit Cost (COGS) in Raw Data
- **Limitation:** The primary dataset (UCI Online Retail II) records realized selling prices in GBP, but contains **zero wholesale cost or margin data**.
- **Policy:**
  - The engine **never fabricates or hallucinates unit costs**.
  - For `objective="revenue"`, unit cost is optional.
  - For `objective="profit"`, valid unit cost ($c > 0$) must be explicitly supplied in the request. If missing, the engine **fails closed** with an actionable input validation error.
  - If a synthetic unit cost is supplied in test fixtures or demonstration scenarios, the output is explicitly flagged `is_synthetic = True` and must not be reported as a real commercial result.

### 2.4 Absence of Real-Time Competitor Price Scrapes
- **Limitation:** Historical transaction datasets lack competitor price observations.
- **Policy:**
  - Competitor-relative constraints (e.g. `max_competitor_price_premium_pct`) are applied **only if a genuine, validated competitor observation is supplied**.
  - If no competitor observation exists, the rule is safely skipped without inventing fake competitor benchmarks.

### 2.5 Extrapolation Outside Historical Support
- **Limitation:** Machine learning models (especially decision trees and non-linear regressors) degrade unpredictably when evaluated far outside the minimum and maximum prices observed in training data.
- **Policy:**
  - The engine audits candidate prices against historical support $[\min(P_{\text{train}}), \max(P_{\text{train}})]$.
  - Under `extrapolation_policy="warn"`, out-of-support candidates trigger clear warning advisories.
  - Under `extrapolation_policy="reject"`, out-of-support candidates are marked infeasible and excluded from recommendation.

---

## 3. Conditions Under Which Optimization is Blocked or Forbidden

The optimizer will deliberately refuse to produce an actionable recommendation under the following conditions:

| Condition | Engine Response / Status | Rationale |
| :--- | :--- | :--- |
| **Missing Unit Cost for Profit** | Fails closed (`INPUT_VALIDATION_ERROR`) | Profit cannot be computed without cost; fabricating costs violates data integrity. |
| **Price-Invariant Demand Model** | Halts (`PRICE_INVARIANT_MODEL`) | Prevents trivial, ungrounded selection of maximum price bounds. |
| **All Candidates Infeasible** | Returns `NO_FEASIBLE_CANDIDATE` | All generated prices violate at least one hard constraint (e.g. margin floor, movement limit). |
| **Inverted or Non-Positive Bounds** | Fails closed (`INPUT_VALIDATION_ERROR`) | $P_{\min} \le 0$ or $P_{\min} > P_{\max}$ is mathematically invalid. |
| **Non-Finite Inputs** | Fails closed (`INPUT_VALIDATION_ERROR`) | NaN or infinite values are rejected. |

---

## 4. Human Approval Governance

In accordance with Phase 3 specifications:
- `human_approval_required: true` is hardcoded across all recommendation payloads.
- Automated repricing is strictly disabled (`auto_reprice_enabled: false`).
- All recommendations must be reviewed and approved by human pricing managers before any production action.
