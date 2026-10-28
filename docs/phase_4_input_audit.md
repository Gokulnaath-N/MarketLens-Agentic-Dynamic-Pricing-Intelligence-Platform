# MarketLens AI — Phase 4 Input & Environment Audit
Agentic Market Intelligence Prerequisites and Data Readiness Audit

**Document Version:** 1.0.0  
**Audit Date:** 2026-10-28  
**Author:** Agentic AI Architect & Senior Data Engineer  
**Status:** COMPLETE & VERIFIED  

---

## 1. Executive Summary

This audit assesses the state of the repository, acquired datasets, and LLM configuration before implementing the Phase 4 **Agentic Market Intelligence Workflows** (Customer Review Insights, Competitor Monitoring, and Validated Signal Aggregation).

In accordance with MarketLens AI principles (Principle 1: *No fabricated market data*, Principle 2: *Keep synthetic data separate*, Principle 6: *LLMs interpret language; code handles exact calculations*, and Principle 12: *Graceful no-key mode*), this document records the ground truth of what actually exists in the local environment.

---

## 2. Audit Findings Against Mandatory Questions

### Q1. Which real review datasets are actually present?
- **Finding:** Currently, **no real customer review dataset is downloaded in the local repository**.
- **Dataset Analysis:**
  - The primary acquired dataset is **UCI Online Retail II** (`data/raw/uci_online_retail_ii/online_retail_II.xlsx`), which contains transaction logs (`Invoice`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `Price`, `Customer ID`, `Country`), but does **not** contain customer review text, review timestamps, or numerical 1–5 star ratings.
  - While candidate source `olist_brazilian_ecommerce` is documented in `data/manifests/dataset_candidate_inventory.json` as having customer reviews, it was not downloaded in Phase 1 due to authentication and licensing restrictions (CC BY-NC-SA 4.0, non-commercial only).
- **Architectural Policy:** We **do not invent or fabricate customer reviews**. We implement the typed review ingestion contract, structured Pydantic schemas, prompt templates, rule-based lexicon extractors, and mock adapters. Real-data execution against an external review corpus is documented as blocked pending acquisition of an approved public review source (such as an open subset of Olist or Amazon Reviews 2023).

### Q2. Do genuine competitor price observations exist?
- **Finding:** **No genuine competitor price observations exist** in the raw repository data.
- **Analysis:** Real retail sales transaction prices in `sales_observations.parquet` represent the merchant's own realized historical prices in GBP, not competitor observations.
- **Architectural Policy:** A retail transaction price is never relabeled as a competitor price. The Competitor Monitoring Workflow is implemented as a deterministic Python engine and verified using clearly labeled synthetic test fixtures (`is_synthetic = True`). The source contract for genuine future competitor feeds is formally established.

### Q3. Does data have reliable product IDs and timestamps suitable for linking reviews?
- **Finding:** The canonical catalog (`product_catalog.parquet`) establishes unique SKU identifiers (`uci_<StockCode>`) and transaction timestamps. Any review dataset to be linked must share or verifiably map to these product IDs and include explicit review creation timestamps (`review_created_at` / `review_available_at`) to prevent future lookahead leakage into sales forecast periods.

### Q4. Which LLM service abstraction and provider configuration exist?
- **Configuration:** `configs/agents.yaml` defines:
  - `agents_enabled: false` (disabled by default for safe offline execution)
  - `default_provider: "mock"` (options: `mock`, `gemini`, `openai`)
  - `request_timeout_seconds: 30`
  - `max_retries: 2`
  - `log_prompts_and_responses: false` (to prevent PII leakage)
- **Environment Variables:** `.env.example` specifies placeholders (`GEMINI_API_KEY`, `OPENAI_API_KEY`), but no live API keys are committed or present.
- **Implementation Strategy:** Build `src/marketlens/llm/` with a provider-neutral interface (`BaseLLMService`), a deterministic `MockLLMService`, a rule-based `RuleBasedReviewExtractor`, and a configuration factory (`get_llm_service`). The system operates 100% offline without requiring paid API keys.

### Q5. Which persistence mechanisms are implemented and usable?
- **Storage Conventions:** Phase 1 and 2 established Parquet and JSONL storage under `data/processed/` and `data/manifests/`.
- **Policy:** Persist validated review signals, competitor change events, and market aggregates as structured Parquet or JSONL files accompanied by run metadata manifests (tracking run ID, input counts, valid/failed counts, and checksums).

### Q6. Which Phase 2/3 feature contracts must be preserved?
- Phase 2 weekly grain `W-MON`, target `units_sold`, and `period_start` time indices.
- Phase 3 optimization request/result contracts and the Pricing Validity Gate.
- Signal aggregation must output time-aligned feature frames keyed by `(product_id, period_start)` matching Phase 2.

### Q7. What functionality can be completed now vs. blocked?
- **Can Be Completed & Verified:**
  1. Typed Pydantic schemas for review inputs, review insight outputs, competitor observations, competitor change events, and aggregated market signals.
  2. Prompt templates and injection defenses.
  3. Deterministic rule-based and mock review analysis workflows.
  4. Deterministic competitor price change detection and threshold alerts.
  5. Time-aligned, leakage-safe market signal aggregation.
  6. Comprehensive unit and integration test suites.
- **Blocked Pending External Sources/Credentials:**
  1. Live external LLM API calls (requires user-provided `GEMINI_API_KEY` or `OPENAI_API_KEY`).
  2. Production review extraction on real UCI data (because UCI lacks reviews).
  3. Real-world competitor price change monitoring (because real competitor feeds are absent).

### Q8. Privacy and licensing limitations affecting external LLM calls
- Customer review text can inadvertently contain reviewer names, emails, addresses, or order IDs.
- The Review Insights workflow must apply regex-based privacy minimization (redacting emails, phone numbers, and potential personal identifiers) before text is dispatched to external LLM providers.
- Output logs must strictly truncate or suppress raw review text to prevent PII exposure in application logs.
