"""Unit tests for chronological train/validation/test splitting."""

from __future__ import annotations

import pandas as pd
import pytest

from marketlens.data.split import SplitValidationError, chronological_split


@pytest.fixture
def multi_period_df() -> pd.DataFrame:
    dates = pd.date_range("2026-01-05", periods=20, freq="W-MON")
    return pd.DataFrame(
        {
            "product_id": ["uci_101"] * 20,
            "period_start": dates,
            "units_sold": [float(i * 10) for i in range(20)],
        }
    )


class TestChronologicalSplit:
    """Tests temporal splitting and boundary validation."""

    def test_chronological_ordering_guarantee(self, multi_period_df: pd.DataFrame):
        train, val, test, meta = chronological_split(
            multi_period_df,
            time_col="period_start",
            train_ratio=0.70,
            val_ratio=0.15,
            test_ratio=0.15,
        )

        assert len(train) + len(val) + len(test) == 20
        assert not train.empty
        assert not val.empty
        assert not test.empty

        # Strict chronological boundaries: max(train) < min(val) and max(val) < min(test)
        assert train["period_start"].max() < val["period_start"].min()
        assert val["period_start"].max() < test["period_start"].min()

        assert meta["train"]["period_count"] > 0
        assert meta["validation"]["period_count"] > 0
        assert meta["test"]["period_count"] > 0

    def test_explicit_split_dates(self, multi_period_df: pd.DataFrame):
        train, val, test, meta = chronological_split(
            multi_period_df,
            time_col="period_start",
            train_end="2026-03-02",
            val_end="2026-04-13",
        )
        assert train["period_start"].max() <= pd.Timestamp("2026-03-02")
        assert val["period_start"].max() <= pd.Timestamp("2026-04-13")
        assert val["period_start"].min() > pd.Timestamp("2026-03-02")
        assert test["period_start"].min() > pd.Timestamp("2026-04-13")

    def test_too_few_periods_raises_error(self):
        short_df = pd.DataFrame(
            {
                "period_start": pd.to_datetime(["2026-01-01", "2026-01-02"]),
                "units_sold": [10.0, 20.0],
            }
        )
        with pytest.raises(SplitValidationError, match="Too few distinct time periods"):
            chronological_split(short_df)
