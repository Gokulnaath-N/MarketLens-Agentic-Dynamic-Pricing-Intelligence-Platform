"""Time-aligned market signal feature generation and dataset merging for demand forecasting."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from marketlens.agents.schemas import (
    ChangeDirection,
    CompetitorChangeEvent,
    CompetitorObservation,
    MarketSignalAggregate,
    ReviewInsightOutput,
    SentimentLabel,
    ValidationStatus,
)
from marketlens.logging_config import get_logger

logger = get_logger("marketlens.features.market_signals")


def build_market_signal_features_for_period(
    product_id: str,
    period_start: pd.Timestamp,
    own_price: float,
    reviews: Optional[List[ReviewInsightOutput]] = None,
    competitor_observations: Optional[List[CompetitorObservation]] = None,
    competitor_events: Optional[List[CompetitorChangeEvent]] = None,
    review_window_days: int = 30,
    competitor_window_days: int = 7,
) -> Dict[str, Union[float, int]]:
    """Generate time-aligned review and competitor features for a specific product and period start.

    Temporal Leakage Prevention Rule:
        The forecast origin is at period_start (e.g. Monday 00:00:00 UTC).
        Any review or competitor observation with timestamp strictly > period_start is purged.
        Observations older than their respective lookback window are excluded.

    Args:
        product_id: Product identifier.
        period_start: Forecast origin period start timestamp.
        own_price: Focal product price at decision time (e.g. price_lag_1).
        reviews: List of extracted review insights.
        competitor_observations: List of competitor price observations.
        competitor_events: List of competitor price change events.
        review_window_days: Lookback window for customer reviews (default 30 days).
        competitor_window_days: Lookback window for competitor prices (default 7 days).

    Returns:
        Dictionary of numerical feature values and missingness flags.
    """
    origin_dt = period_start.to_pydatetime()
    if origin_dt.tzinfo is None:
        origin_dt = origin_dt.replace(tzinfo=timezone.utc)

    # -------------------------------------------------------------
    # 1. Review Feature Extraction (30-day window)
    # -------------------------------------------------------------
    rev_cutoff = origin_dt - timedelta(days=review_window_days)
    eligible_reviews: List[ReviewInsightOutput] = []

    if reviews:
        for r in reviews:
            if r.product_id != product_id:
                continue
            r_ts = r.review_timestamp or r.processed_at
            if r_ts.tzinfo is None:
                r_ts = r_ts.replace(tzinfo=timezone.utc)

            # Strict anti-leakage filter
            if r_ts > origin_dt:
                continue  # Future review!
            if r_ts >= rev_cutoff and r.validation_status != ValidationStatus.FAILED:
                eligible_reviews.append(r)

    review_count_30d = len(eligible_reviews)
    usable_reviews = [r for r in eligible_reviews if r.sentiment_label != SentimentLabel.UNKNOWN]
    usable_count_30d = len(usable_reviews)

    if usable_count_30d >= 1:
        mean_sentiment_30d = float(np.mean([r.sentiment_score for r in usable_reviews]))
        pos_count = sum(1 for r in usable_reviews if r.sentiment_label == SentimentLabel.POSITIVE)
        neg_count = sum(1 for r in usable_reviews if r.sentiment_label == SentimentLabel.NEGATIVE)
        positive_ratio_30d = float(pos_count / usable_count_30d)
        negative_ratio_30d = float(neg_count / usable_count_30d)
        review_signal_missing = 0
    else:
        mean_sentiment_30d = 0.0
        positive_ratio_30d = 0.0
        negative_ratio_30d = 0.0
        review_signal_missing = 1

    aspect_quality_mentions_30d = sum(1 for r in eligible_reviews if "product_quality" in r.aspects)
    aspect_value_mentions_30d = sum(1 for r in eligible_reviews if "value_for_money" in r.aspects)

    # -------------------------------------------------------------
    # 2. Competitor Feature Extraction (7-day window)
    # -------------------------------------------------------------
    comp_cutoff = origin_dt - timedelta(days=competitor_window_days)
    eligible_obs: List[CompetitorObservation] = []

    if competitor_observations:
        for obs in competitor_observations:
            if obs.product_id != product_id:
                continue
            o_ts = obs.observed_at
            if o_ts.tzinfo is None:
                o_ts = o_ts.replace(tzinfo=timezone.utc)

            # Strict anti-leakage filter
            if o_ts > origin_dt:
                continue  # Future price!
            if o_ts >= comp_cutoff and obs.observed_price > 0:
                eligible_obs.append(obs)

    if eligible_obs:
        prices = [o.observed_price for o in eligible_obs]
        unique_competitors = {o.competitor_id for o in eligible_obs}
        competitor_count_7d = len(unique_competitors)
        min_competitor_price_7d = float(min(prices))
        mean_competitor_price_7d = float(np.mean(prices))
        
        # Price gap vs focal product (positive = own price is higher)
        if min_competitor_price_7d > 0:
            price_gap_pct = float(((own_price - min_competitor_price_7d) / min_competitor_price_7d) * 100.0)
        else:
            price_gap_pct = 0.0
        competitor_signal_missing = 0
    else:
        competitor_count_7d = 0
        min_competitor_price_7d = float(own_price) if own_price > 0 else 0.0
        mean_competitor_price_7d = float(own_price) if own_price > 0 else 0.0
        price_gap_pct = 0.0
        competitor_signal_missing = 1

    # Filter events
    eligible_events: List[CompetitorChangeEvent] = []
    if competitor_events:
        for evt in competitor_events:
            if evt.product_id != product_id:
                continue
            e_ts = evt.current_observed_at
            if e_ts.tzinfo is None:
                e_ts = e_ts.replace(tzinfo=timezone.utc)
            if e_ts > origin_dt:
                continue
            if e_ts >= comp_cutoff:
                eligible_events.append(evt)

    if eligible_events:
        sorted_events = sorted(eligible_events, key=lambda e: e.current_observed_at, reverse=True)
        latest_change_pct = float(sorted_events[0].percentage_change)
        price_drop_flag = int(any(e.threshold_exceeded and e.direction == ChangeDirection.DECREASE for e in eligible_events))
    else:
        latest_change_pct = 0.0
        price_drop_flag = 0

    return {
        # Review features
        "review_count_30d": review_count_30d,
        "usable_review_count_30d": usable_count_30d,
        "mean_sentiment_30d": round(mean_sentiment_30d, 4),
        "positive_review_ratio_30d": round(positive_ratio_30d, 4),
        "negative_review_ratio_30d": round(negative_ratio_30d, 4),
        "aspect_quality_mentions_30d": aspect_quality_mentions_30d,
        "aspect_value_mentions_30d": aspect_value_mentions_30d,
        "review_signal_missing": review_signal_missing,
        # Competitor features
        "competitor_count_7d": competitor_count_7d,
        "min_competitor_price_7d": round(min_competitor_price_7d, 4),
        "mean_competitor_price_7d": round(mean_competitor_price_7d, 4),
        "competitor_price_gap_pct": round(price_gap_pct, 4),
        "latest_competitor_price_change_pct": round(latest_change_pct, 4),
        "competitor_price_drop_flag": price_drop_flag,
        "competitor_signal_missing": competitor_signal_missing,
    }


def merge_market_signals(
    demand_df: pd.DataFrame,
    reviews: Optional[List[ReviewInsightOutput]] = None,
    competitor_observations: Optional[List[CompetitorObservation]] = None,
    competitor_events: Optional[List[CompetitorChangeEvent]] = None,
    time_col: str = "period_start",
    product_id_col: str = "product_id",
    price_col: str = "price_lag_1",
) -> pd.DataFrame:
    """Merge time-aligned review perception and competitor signals onto the weekly demand DataFrame.

    Ensures zero temporal leakage by invoking build_market_signal_features_for_period row by row
    based on the exact forecast origin (period_start).
    """
    df = demand_df.copy()
    if price_col not in df.columns:
        # Fallback to mean_unit_price if price_lag_1 not pre-computed
        fallback_col = "mean_unit_price" if "mean_unit_price" in df.columns else None
        p_series = df[fallback_col] if fallback_col else pd.Series(0.0, index=df.index)
    else:
        p_series = df[price_col].fillna(df.get("mean_unit_price", 0.0))

    feature_records = []
    for idx, row in df.iterrows():
        pid = str(row[product_id_col])
        p_start = pd.to_datetime(row[time_col])
        own_p = float(p_series.iloc[idx]) if not pd.isna(p_series.iloc[idx]) else 0.0

        feats = build_market_signal_features_for_period(
            product_id=pid,
            period_start=p_start,
            own_price=own_p,
            reviews=reviews,
            competitor_observations=competitor_observations,
            competitor_events=competitor_events,
        )
        feature_records.append(feats)

    features_df = pd.DataFrame(feature_records, index=df.index)
    merged = pd.concat([df, features_df], axis=1)
    logger.info(f"Successfully merged {features_df.shape[1]} market signal features into demand DataFrame.")
    return merged


def verify_temporal_integrity(
    df: pd.DataFrame,
    future_perturbation_hours: int = 48,
) -> bool:
    """Adversarial check: verify that inserting a future market signal does not alter historical features."""
    test_pid = "TEST-SKU-999"
    t_origin = pd.Timestamp("2026-02-01 00:00:00", tz="UTC")
    
    # 1. Base feature generation
    base_feats = build_market_signal_features_for_period(
        product_id=test_pid,
        period_start=t_origin,
        own_price=20.0,
        reviews=[],
        competitor_observations=[],
    )

    # 2. Insert adversarial future review (48 hours after origin)
    future_review = ReviewInsightOutput(
        review_id="ADV-REV-FUTURE",
        product_id=test_pid,
        sentiment_label=SentimentLabel.NEGATIVE,
        sentiment_score=-0.95,
        summary="Future complaint that must be blocked.",
        extraction_method="mock",
        review_timestamp=t_origin + timedelta(hours=future_perturbation_hours),
    )
    # Insert adversarial future competitor price (24 hours after origin)
    future_obs = CompetitorObservation(
        observation_id="ADV-OBS-FUTURE",
        product_id=test_pid,
        competitor_id="COMPETITOR-X",
        observed_price=5.00,  # 75% price slash
        currency="GBP",
        observed_at=t_origin + timedelta(hours=24),
    )

    perturbed_feats = build_market_signal_features_for_period(
        product_id=test_pid,
        period_start=t_origin,
        own_price=20.0,
        reviews=[future_review],
        competitor_observations=[future_obs],
    )

    # The historical features at t_origin must be 100% IDENTICAL
    for k in base_feats:
        if base_feats[k] != perturbed_feats[k]:
            logger.error(f"Temporal leakage detected on feature '{k}': {base_feats[k]} != {perturbed_feats[k]}")
            return False

    return True
