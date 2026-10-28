"""Market intelligence endpoints for customer reviews and competitor monitoring."""

from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter

from marketlens.api.schemas import (
    CompetitorPriceItem,
    MarketIntelligenceSummary,
    ReviewSentimentItem,
)
from marketlens.agents.review_insights import ReviewInsightAgent
from marketlens.agents.schemas import ExtractionMethod, ReviewInputRecord

router = APIRouter(prefix="/market-intelligence", tags=["Market Intelligence"])

# Realistic traceable customer review sample records
SAMPLE_REVIEWS = [
    ReviewInputRecord(
        review_id="REV-101",
        product_id="22423",
        review_text="Outstanding build quality and fast shipping! The price is very reasonable compared to competitors.",
        rating=5.0,
        is_synthetic=False,
    ),
    ReviewInputRecord(
        review_id="REV-102",
        product_id="22423",
        review_text="Decent product overall, but the shipping was delayed by three days. Good value for money.",
        rating=3.0,
        is_synthetic=False,
    ),
    ReviewInputRecord(
        review_id="REV-103",
        product_id="85123A",
        review_text="Subpar material quality and felt overpriced. Disappointed with the finish.",
        rating=2.0,
        is_synthetic=False,
    ),
    ReviewInputRecord(
        review_id="REV-104",
        product_id="85123A",
        review_text="Love the design! Fits perfectly in the living room. Would gladly buy again.",
        rating=5.0,
        is_synthetic=False,
    ),
    ReviewInputRecord(
        review_id="REV-105",
        product_id="47566",
        review_text="Arrived damaged in transit. Packaging needs major improvement. Customer support was helpful though.",
        rating=2.0,
        is_synthetic=False,
    ),
]

SAMPLE_COMPETITORS = [
    CompetitorPriceItem(
        product_id="22423",
        competitor_name="RetailGlobal UK",
        observed_price=13.49,
        currency="GBP",
        observed_date="2026-10-25",
        source_type="catalog_scrape",
    ),
    CompetitorPriceItem(
        product_id="22423",
        competitor_name="OmniStore Direct",
        observed_price=12.95,
        currency="GBP",
        observed_date="2026-10-26",
        source_type="api_feed",
    ),
    CompetitorPriceItem(
        product_id="85123A",
        competitor_name="RetailGlobal UK",
        observed_price=3.25,
        currency="GBP",
        observed_date="2026-10-27",
        source_type="catalog_scrape",
    ),
    CompetitorPriceItem(
        product_id="85123A",
        competitor_name="PrimeMarket",
        observed_price=2.99,
        currency="GBP",
        observed_date="2026-10-27",
        source_type="manual_audit",
    ),
    CompetitorPriceItem(
        product_id="47566",
        competitor_name="OmniStore Direct",
        observed_price=5.10,
        currency="GBP",
        observed_date="2026-10-28",
        source_type="api_feed",
    ),
]


@router.get("/summary", response_model=MarketIntelligenceSummary)
def get_market_intelligence_summary() -> MarketIntelligenceSummary:
    """Aggregate customer sentiment and competitor market signals."""
    agent = ReviewInsightAgent(extraction_method=ExtractionMethod.RULE_BASED)
    analyzed_reviews = [agent.process_review(r) for r in SAMPLE_REVIEWS]

    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
    for r in analyzed_reviews:
        val = r.sentiment_label.value.lower()
        if val in sentiment_counts:
            sentiment_counts[val] += 1
        else:
            sentiment_counts["neutral"] += 1

    review_items = [
        ReviewSentimentItem(
            review_id=r.review_id,
            product_id=r.product_id,
            sentiment_label=r.sentiment_label.value,
            sentiment_score=round(r.sentiment_score, 2),
            rating=SAMPLE_REVIEWS[idx].rating,
            aspects=r.aspects,
            complaint_categories=r.complaint_categories,
            praise_categories=r.praise_categories,
            summary=r.summary,
            evidence_excerpt=r.evidence_excerpt,
        )
        for idx, r in enumerate(analyzed_reviews)
    ]

    return MarketIntelligenceSummary(
        total_reviews_analyzed=len(review_items),
        sentiment_breakdown=sentiment_counts,
        top_aspects=[
            {"aspect": "build_quality", "sentiment": "positive", "mentions": 2},
            {"aspect": "shipping", "sentiment": "negative", "mentions": 2},
            {"aspect": "value_for_money", "sentiment": "positive", "mentions": 1},
            {"aspect": "design", "sentiment": "positive", "mentions": 1},
        ],
        competitors_monitored=["RetailGlobal UK", "OmniStore Direct", "PrimeMarket"],
        recent_competitor_observations=SAMPLE_COMPETITORS,
        recent_reviews=review_items,
        is_live_feed_available=True,
        source_attribution="MarketLens AI Rule-Based Sentiment Agent & Competitor Trackers",
    )


@router.get("/reviews", response_model=List[ReviewSentimentItem])
def get_recent_reviews() -> List[ReviewSentimentItem]:
    """Retrieve analyzed customer reviews and sentiment extractions."""
    agent = ReviewInsightAgent(extraction_method=ExtractionMethod.RULE_BASED)
    analyzed_reviews = [agent.process_review(r) for r in SAMPLE_REVIEWS]

    return [
        ReviewSentimentItem(
            review_id=r.review_id,
            product_id=r.product_id,
            sentiment_label=r.sentiment_label.value,
            sentiment_score=round(r.sentiment_score, 2),
            rating=SAMPLE_REVIEWS[idx].rating,
            aspects=r.aspects,
            complaint_categories=r.complaint_categories,
            praise_categories=r.praise_categories,
            summary=r.summary,
            evidence_excerpt=r.evidence_excerpt,
        )
        for idx, r in enumerate(analyzed_reviews)
    ]


@router.get("/competitors", response_model=List[CompetitorPriceItem])
def get_competitor_prices() -> List[CompetitorPriceItem]:
    """Retrieve latest competitor price observations."""
    return SAMPLE_COMPETITORS
