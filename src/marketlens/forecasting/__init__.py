"""MarketLens AI Forecasting Module.

Demand forecasting models, baseline forecasters, metrics, and evaluation pipeline.
"""

from marketlens.forecasting.baselines import (
    BaseForecaster,
    MovingAverageForecaster,
    NaiveLastObservedForecaster,
    RandomForestDemandForecaster,
    RidgeRegressionForecaster,
)
from marketlens.forecasting.evaluate import train_and_evaluate_models
from marketlens.forecasting.metrics import compute_forecasting_metrics

__all__ = [
    "BaseForecaster",
    "MovingAverageForecaster",
    "NaiveLastObservedForecaster",
    "RandomForestDemandForecaster",
    "RidgeRegressionForecaster",
    "compute_forecasting_metrics",
    "train_and_evaluate_models",
]
