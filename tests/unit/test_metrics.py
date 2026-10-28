"""Unit tests for forecasting evaluation metrics and zero-division handling."""

from __future__ import annotations

import numpy as np
import pytest

from marketlens.forecasting.metrics import compute_forecasting_metrics


class TestForecastingMetrics:
    """Tests metric arithmetic against hand-computed ground truth."""

    def test_perfect_prediction_metrics(self):
        y_true = np.array([10.0, 20.0, 30.0])
        y_pred = np.array([10.0, 20.0, 30.0])
        metrics = compute_forecasting_metrics(y_true, y_pred)

        assert metrics["mae"] == 0.0
        assert metrics["rmse"] == 0.0
        assert metrics["wape"] == 0.0
        assert metrics["r2"] == 1.0

    def test_hand_calculated_metrics(self):
        # Errors: |10 - 12| = 2, |20 - 16| = 4 -> mean error = 3.0
        # RMSE: sqrt((4 + 16)/2) = sqrt(10) ≈ 3.1623
        # WAPE: (2 + 4) / (10 + 20) = 6 / 30 = 0.20
        y_true = np.array([10.0, 20.0])
        y_pred = np.array([12.0, 16.0])
        y_train = np.array([5.0, 10.0]) # diff = 5.0 -> MASE = 3.0 / 5.0 = 0.60
        metrics = compute_forecasting_metrics(y_true, y_pred, y_train=y_train)

        assert pytest.approx(metrics["mae"], 0.001) == 3.0
        assert pytest.approx(metrics["rmse"], 0.001) == 3.1623
        assert pytest.approx(metrics["wape"], 0.001) == 0.20
        assert pytest.approx(metrics["mase"], 0.001) == 0.60

    def test_zero_denominator_actuals_safe(self):
        # All actuals are 0
        y_true = np.array([0.0, 0.0, 0.0])
        y_pred = np.array([1.0, 2.0, 1.0])
        metrics = compute_forecasting_metrics(y_true, y_pred)

        assert metrics["mae"] == pytest.approx(1.3333, 0.001)
        assert metrics["wape"] == 0.0 # Handled zero-division safely without error
        assert isinstance(metrics["r2"], float)

    def test_empty_arrays_safe(self):
        metrics = compute_forecasting_metrics([], [])
        assert metrics["mae"] == 0.0
        assert metrics["rmse"] == 0.0
