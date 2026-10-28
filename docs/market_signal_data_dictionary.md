# MarketLens AI — Market Signal Data Dictionary

**Document Version:** 1.0.0  
**Phase:** Phase 4 (Agentic Market Intelligence)  
**Status:** Approved & Implemented  
**Date:** 2026-10-28  

---

## 1. Overview

This data dictionary defines the canonical schemas, data types, constraints, and missing-value policies for MarketLens AI Phase 4 market intelligence workflows. All structures are programmatically validated via Pydantic in [schemas.py](file:///d:/Professional%20Projects/Agentic_Dynammic_Intelligence_Platform/src/marketlens/agents/schemas.py).

---

## 2. Table: Review Input Record (`ReviewInputRecord`)

Raw or preprocessed customer feedback ingested from external review sources.

| Column Name | Data Type | Nullable | Valid Range / Format | Semantic Description |
| :--- | :--- | :--- | :--- | :--- |
| `review_id` | `string` | No | Non-empty | Unique review identifier from source or deterministic hash. |
| `product_id` | `string` | No | Namespaced SKU | Source-scoped product identifier (e.g. `uci_85123A`). |
| `review_text` | `string` | No | Max 4,000 chars | Customer feedback text (sanitized and PII-redacted). |
| `review_timestamp` | `datetime` | Yes | ISO 8601 UTC | Timestamp review was written/published. |
| `rating` | `float` | Yes | `[1.0, 5.0]` | Numerical star rating on standard 1-to-5 scale. |
| `source_name` | `string` | No | Identifier | Originating source dataset or feed ID. |
| `is_synthetic` | `bool` | No | `true / false` | Flags synthetic test fixtures. Never mixed with real data. |

---

## 3. Table: Review Insight Output (`ReviewInsightOutput`)

Structured customer perception signals extracted from a single review.

| Column Name | Data Type | Nullable | Valid Range / Format | Semantic Description |
| :--- | :--- | :--- | :--- | :--- |
| `review_id` | `string` | No | Matches input | Review identifier. |
| `product_id` | `string` | No | Matches input | Product identifier. |
| `sentiment_label` | `enum` | No | `positive`, `neutral`, `negative`, `mixed`, `unknown` | Discrete sentiment classification. |
| `sentiment_score` | `float` | No | `[-1.0, 1.0]` | Normalized sentiment intensity score. |
| `aspects` | `list[str]` | No | Controlled categories | Detected aspects (`product_quality`, `value_for_money`, `delivery_shipping`, `customer_service`, `packaging`). |
| `complaint_categories` | `list[str]` | No | Controlled categories | Extracted dissatisfaction drivers (`perceived_low_quality`, `perceived_high_price`, `delivery_delay_or_damage`, etc.). |
| `praise_categories` | `list[str]` | No | Controlled categories | Extracted satisfaction drivers (`high_product_satisfaction`, `good_value_for_money`). |
| `summary` | `string` | No | Text | Concise evidence-grounded summary. |
| `evidence_excerpt` | `string` | Yes | Max 150 chars | Verbatim excerpt from source text supporting classification. |
| `extraction_method` | `enum` | No | `rule_based`, `mock`, `llm` | Provenance of the extraction mechanism used. |
| `validation_status` | `enum` | No | `validated`, `needs_review`, `failed` | Schema and quality validation status. |
| `is_synthetic` | `bool` | No | `true / false` | Synthetic data flag. |

---

## 4. Table: Competitor Price Observation (`CompetitorObservation`)

Discrete point-in-time scrape or log of a competitor's selling price.

| Column Name | Data Type | Nullable | Valid Range / Format | Semantic Description |
| :--- | :--- | :--- | :--- | :--- |
| `observation_id` | `string` | No | Non-empty | Unique observation record ID. |
| `product_id` | `string` | No | Namespaced SKU | Mapped internal product key. |
| `competitor_id` | `string` | No | Identifier | Competitor retailer identifier. |
| `observed_price` | `float` | No | Finite $> 0$ | Observed price in specified currency. |
| `currency` | `string` | No | ISO 4217 (3 letters) | Transaction currency (e.g. `GBP`). |
| `observed_at` | `datetime` | No | ISO 8601 UTC | Timestamp price was captured. |
| `is_synthetic` | `bool` | No | `true / false` | Synthetic simulation flag. |

---

## 5. Table: Competitor Change Event (`CompetitorChangeEvent`)

Deterministic price movement metrics calculated between two sequential observations.

| Column Name | Data Type | Nullable | Formula / Format | Semantic Description |
| :--- | :--- | :--- | :--- | :--- |
| `event_id` | `string` | No | Deterministic key | Composite ID: `evt_<prev_id>_<curr_id>`. |
| `previous_price` | `float` | No | $> 0$ | Price at $t_{\text{prev}}$. |
| `current_price` | `float` | No | $> 0$ | Price at $t_{\text{curr}}$. |
| `absolute_change`| `float` | No | $p_{\text{curr}} - p_{\text{prev}}$ | Absolute price difference. |
| `percentage_change`| `float` | No | $100 \cdot \frac{p_{\text{curr}} - p_{\text{prev}}}{p_{\text{prev}}}$ | Percentage price movement. |
| `direction` | `enum` | No | `increase`, `decrease`, `unchanged` | Movement direction. |
| `threshold_exceeded`| `bool` | No | $\|\Delta\%\| \ge \text{threshold}$ | Alert flag when change meets or exceeds threshold. |
| `age_hours` | `float` | No | $\frac{t_{\text{curr}} - t_{\text{prev}}}{3600}$ | Time elapsed between observations in hours. |
| `is_stale` | `bool` | No | `age_hours > max_age` | Indicates observation gap exceeds freshness limit. |

---

## 6. Table: Market Signal Aggregate (`MarketSignalAggregate`)

Time-aligned canonical feature record keyed by `(product_id, as_of_timestamp)` for demand forecasting.

| Column Name | Data Type | Nullable | Lookback Window | Semantic Description |
| :--- | :--- | :--- | :--- | :--- |
| `product_id` | `string` | No | N/A | Namespaced SKU key. |
| `as_of_timestamp` | `datetime` | No | Forecast Origin | Timestamp representing decision point (Monday 00:00:00 UTC). |
| `review_count` | `int` | No | Trailing 30 days | Total reviews recorded in lookback window. |
| `usable_review_count`| `int` | No | Trailing 30 days | Total reviews with non-unknown sentiment. |
| `mean_sentiment_score`| `float` | Yes | Trailing 30 days | Mean score across usable reviews. Null if count is 0. |
| `positive_review_ratio`| `float` | Yes | Trailing 30 days | Positive reviews / usable reviews. |
| `negative_review_ratio`| `float` | Yes | Trailing 30 days | Negative reviews / usable reviews. |
| `aspect_counts` | `dict` | No | Trailing 30 days | Frequency mapping of aspect mentions. |
| `complaint_counts` | `dict` | No | Trailing 30 days | Frequency mapping of complaint types. |
| `competitor_count` | `int` | No | Trailing 7 days | Discrete competitors observed. |
| `min_competitor_price`| `float` | Yes | Trailing 7 days | Lowest active competitor price. |
| `mean_competitor_price`| `float` | Yes | Trailing 7 days | Average active competitor price. |
| `max_competitor_price`| `float` | Yes | Trailing 7 days | Highest active competitor price. |
| `latest_competitor_price_change_pct`| `float` | Yes | Trailing 7 days | Most recent percentage change among competitors. |
| `competitor_price_drop_flag`| `bool` | No | Trailing 7 days | True if any competitor decreased price by $\ge 5\%$. |
| `quality_status` | `enum` | No | Current | `AVAILABLE`, `MISSING`, `INSUFFICIENT_SAMPLE`, `STALE`, `SYNTHETIC_ONLY`. |
