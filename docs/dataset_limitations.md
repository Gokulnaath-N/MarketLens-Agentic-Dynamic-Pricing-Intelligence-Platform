# MarketLens AI — Dataset Limitations & Truthfulness Declaration

**Document Version:** 1.0.0  
**Phase:** Phase 2 (Canonical Modeling & Demand Forecasting)  
**Status:** Approved & Implemented  
**Date:** 2026-10-28  

---

## 1. Principle of Empirical Truthfulness

A core architectural tenet of MarketLens AI is **strict data truthfulness**:
> *Real models must be evaluated against real data. Synthetic features must never be fabricated to artificially inflate model metrics or claim non-existent capabilities.*

This document provides a formal accounting of the data available in the primary dataset (**UCI Online Retail II**) versus the broader commercial intelligence requirements outlined in the MarketLens AI Knowledge Base.

---

## 2. Feature Availability Audit

| Commercial Capability | Required Feature | Present in Raw Data? | Status in Phase 2 | Architectural Treatment |
| :--- | :--- | :--- | :--- | :--- |
| **Demand Forecasting** | Transaction timestamp | **Yes** (`InvoiceDate`) | Fully Utilized | Aggregated to Monday weekly periods (`W-MON`). |
| | Product identifier | **Yes** (`StockCode`) | Fully Utilized | Namespaced canonical key (`uci_<StockCode>`). |
| | Unit sales volume | **Yes** (`Quantity`) | Fully Utilized | Cleaned of returns, regularized with zero-demand filling. |
| | Observed unit price | **Yes** (`Price`) | Fully Utilized | Weighted average realized sales price per week. |
| **Competitor Intelligence** | Competitor price scrapes | **No** | **Absent** | Not present in UCI dataset. **No synthetic competitor prices fabricated.** |
| | Competitor stock availability | **No** | **Absent** | Not present in UCI dataset. |
| **Sentiment Analysis** | Customer review text | **No** | **Absent** | Only transactional product descriptions exist. |
| | Rating scores (1-5 stars) | **No** | **Absent** | Not present in UCI dataset. |
| **Unit Economics** | Wholesale COGS (cost) | **No** | **Absent** | Not present in UCI dataset. |
| | Shipping / handling costs | **No** | **Absent** | Not present in UCI dataset. |

---

## 3. What Can and Cannot Be Learned from Available Data

### What Can Be Learned:
1. **Autoregressive Demand Dynamics:** Weekly momentum, autocorrelation patterns, and recent sales velocity.
2. **Catalog-Wide Temporal Patterns:** Seasonality, holiday shopping surges (e.g., Q4 retail peak in November/December), and post-holiday lulls.
3. **Internal Price Sensitivity (Observed Range):** Empirical elasticity within the merchant's historical price variations for high-frequency items.
4. **Intermittent Demand Patterns:** Transition probabilities between active and zero-demand weeks for long-tail retail catalog items.

### What Cannot Be Learned:
1. **Cross-Price Elasticity with Competitors:** Because competitor pricing was not recorded at transaction time, cross-price elasticity cannot be empirically fitted or measured from this data.
2. **Causal Elasticity vs. Observational Correlation:** Historical price changes in the data may be confounded by promotions, clearance sales of dying items, or bulk tiering.
3. **Gross Margin Optimization:** Without unit wholesale costs (COGS), actual profit margins cannot be calculated from raw transactions alone.

---

## 4. Phase 3 & Beyond Integration Strategy

To fulfill the end-to-end multi-agent vision (Agentic Dynamic Pricing) in subsequent phases:
1. **Configurable Economic Assumptions:** Wholesale cost margins will be parameterized via explicit user configuration (e.g. `cogs_margin_ratio: 0.60`) rather than hallucinated into the historical observation table.
2. **Explicit Simulation Environments:** When testing competitor-aware reinforcement learning or Bayesian pricing agents, market simulations will be explicitly tagged as `SIMULATED_ENVIRONMENT` with configurable opponent reaction functions.
3. **External Real-Time Scrapers / Feeds:** Live sentiment APIs or synthetic competitor feeds will feed dedicated Phase 4 agent tools with distinct provenance manifests.
