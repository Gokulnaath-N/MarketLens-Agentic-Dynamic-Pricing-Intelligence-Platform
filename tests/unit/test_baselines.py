"""Unit tests for baseline demand forecasters."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from marketlens.forecasting.baselines import (
    MovingAverageForecaster,
    NaiveLastObservedForecaster,
    RandomForestDemandForecaster,
    RidgeRegressionForecaster,
)


@pytest.fixture
def train_test_pair() -> tuple[pd.DataFrame, pd.DataFrame]:
    train = pd.DataFrame(
        {
            "target_lag_1": [10.0, 15.0, 20.0, 25.0],
            "rolling_mean_4": [10.0, 12.5, 15.0, 17.5],
            "price_lag_1": [5.0, 5.0, 5.0, 5.0],
            "units_sold": [15.0, 20.0, 25.0, 30.0],
        }
    )
    test = pd.DataFrame(
        {
            "target_lag_1": [30.0, 35.0],
            "rolling_mean_4": [22.5, 27.5],
            "price_lag_1": [5.0, 5.0],
            "units_sold": [35.0, 40.0],
        }
    )
    return train, test


class TestBaselineForecasters:
    """Tests model prediction behavior and constraint enforcement."""

    def test_naive_forecaster(self, train_test_pair):
        train, test = train_test_pair
        forecaster = NaiveLastObservedForecaster(lag_col="target_lag_1")
        preds = forecaster.fit(train, "units_sold", ["target_lag_1"]).predict(test, ["target_lag_1"])
        assert len(preds) == 2
        assert list(preds) == [30.0, 35.0]

    def test_moving_average_forecaster(self, train_test_pair):
        train, test = train_test_pair
        forecaster = MovingAverageForecaster(rolling_col="rolling_mean_4")
        preds = forecaster.fit(train, "units_sold", ["rolling_mean_4"]).predict(test, ["rolling_mean_4"])
        assert list(preds) == [22.5, 27.5]

    def test_ridge_regression_forecaster(self, train_test_pair):
        train, test = train_test_pair
        features = ["target_lag_1", "rolling_mean_4", "price_lag_1"]
        forecaster = RidgeRegressionForecaster(alpha=1.0)
        forecaster.fit(train, "units_sold", features)
        preds = forecaster.predict(test, features)

        assert len(preds) == 2
        # All demand predictions must be non-negative
        assert (preds >= 0.0).all()

    def test_random_forest_forecaster(self, train_test_pair):
        train, test = train_test_pair
        features = ["target_lag_1", "rolling_mean_4", "price_lag_1"]
        forecaster = RandomForestDemandForecaster(n_estimators=10, max_depth=3, random_state=42)
        forecaster.fit(train, "units_sold", features)
        preds = forecaster.predict(test, features)

        assert len(preds) == 2
        assert (preds >= 0.0).all()
