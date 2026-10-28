"""Baseline demand forecasting models: Naive, Moving Average, and Scikit-Learn ML."""

from __future__ import annotations

from typing import List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge


class BaseForecaster:
    """Abstract interface for demand forecasters."""

    def fit(self, train_df: pd.DataFrame, target_col: str, feature_cols: List[str]) -> BaseForecaster:
        return self

    def predict(self, test_df: pd.DataFrame, feature_cols: List[str]) -> np.ndarray:
        raise NotImplementedError


class NaiveLastObservedForecaster(BaseForecaster):
    """Predicts target to be equal to the most recent observed lag (target_lag_1)."""

    def __init__(self, lag_col: str = "target_lag_1"):
        self.lag_col = lag_col

    def fit(self, train_df: pd.DataFrame, target_col: str, feature_cols: List[str]) -> NaiveLastObservedForecaster:
        return self

    def predict(self, test_df: pd.DataFrame, feature_cols: List[str]) -> np.ndarray:
        if self.lag_col in test_df.columns:
            preds = test_df[self.lag_col].fillna(0.0).values
        else:
            preds = np.zeros(len(test_df))
        return np.clip(preds, a_min=0.0, a_max=None)


class MovingAverageForecaster(BaseForecaster):
    """Predicts target to be the recent rolling historical mean (e.g. rolling_mean_4)."""

    def __init__(self, rolling_col: str = "rolling_mean_4"):
        self.rolling_col = rolling_col

    def fit(self, train_df: pd.DataFrame, target_col: str, feature_cols: List[str]) -> MovingAverageForecaster:
        return self

    def predict(self, test_df: pd.DataFrame, feature_cols: List[str]) -> np.ndarray:
        if self.rolling_col in test_df.columns:
            preds = test_df[self.rolling_col].fillna(0.0).values
        else:
            preds = np.zeros(len(test_df))
        return np.clip(preds, a_min=0.0, a_max=None)


class RidgeRegressionForecaster(BaseForecaster):
    """Regularized linear regression demand model using temporal and price features."""

    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self.model = Ridge(alpha=alpha)
        self.fitted_ = False

    def fit(self, train_df: pd.DataFrame, target_col: str, feature_cols: List[str]) -> RidgeRegressionForecaster:
        # Impute any missing lag values in training with 0
        X = train_df[feature_cols].fillna(0.0).values
        y = train_df[target_col].values
        self.model.fit(X, y)
        self.fitted_ = True
        return self

    def predict(self, test_df: pd.DataFrame, feature_cols: List[str]) -> np.ndarray:
        if not self.fitted_:
            raise RuntimeError("Model must be fitted before predict.")
        X = test_df[feature_cols].fillna(0.0).values
        preds = self.model.predict(X)
        return np.clip(preds, a_min=0.0, a_max=None)


class RandomForestDemandForecaster(BaseForecaster):
    """Random Forest regressor capturing non-linear interactions across lag and calendar features."""

    def __init__(self, n_estimators: int = 100, max_depth: Optional[int] = 10, random_state: int = 42):
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1,
        )
        self.fitted_ = False

    def fit(self, train_df: pd.DataFrame, target_col: str, feature_cols: List[str]) -> RandomForestDemandForecaster:
        X = train_df[feature_cols].fillna(0.0).values
        y = train_df[target_col].values
        self.model.fit(X, y)
        self.fitted_ = True
        return self

    def predict(self, test_df: pd.DataFrame, feature_cols: List[str]) -> np.ndarray:
        if not self.fitted_:
            raise RuntimeError("Model must be fitted before predict.")
        X = test_df[feature_cols].fillna(0.0).values
        preds = self.model.predict(X)
        return np.clip(preds, a_min=0.0, a_max=None)
