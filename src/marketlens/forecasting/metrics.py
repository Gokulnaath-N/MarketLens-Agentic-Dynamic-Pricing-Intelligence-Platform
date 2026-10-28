"""Evaluation metrics for demand forecasting models with explicit edge-case handling."""

from __future__ import annotations

from typing import Dict, Optional
import numpy as np


def compute_forecasting_metrics(
    y_true: np.ndarray | list[float],
    y_pred: np.ndarray | list[float],
    y_train: Optional[np.ndarray | list[float]] = None,
) -> Dict[str, float]:
    """Calculate MAE, RMSE, WAPE, MASE, and R2 with zero-division safety.

    Args:
        y_true: Ground truth actual demand quantities.
        y_pred: Model predictions for identical test periods.
        y_train: Optional historical training observations (required for MASE naive scaling).

    Returns:
        Dictionary of rounded metrics.
    """
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)

    if len(yt) == 0:
        return {"mae": 0.0, "rmse": 0.0, "wape": 0.0, "mase": 0.0, "r2": 0.0}

    # Ensure predictions are non-negative for demand
    yp = np.clip(yp, a_min=0.0, a_max=None)

    errors = yt - yp
    abs_errors = np.abs(errors)

    # 1. MAE
    mae = float(np.mean(abs_errors))

    # 2. RMSE
    rmse = float(np.sqrt(np.mean(errors ** 2)))

    # 3. WAPE (Weighted Absolute Percentage Error = sum(|y - y_hat|) / sum(y))
    sum_actual = float(np.sum(yt))
    wape = float(np.sum(abs_errors) / sum_actual) if sum_actual > 0 else 0.0

    # 4. MASE (Mean Absolute Scaled Error)
    mase = 0.0
    if y_train is not None and len(y_train) > 1:
        y_tr = np.asarray(y_train, dtype=float)
        # In-sample naive 1-step difference
        mae_naive = float(np.mean(np.abs(np.diff(y_tr))))
        if mae_naive > 0:
            mase = float(mae / mae_naive)

    # 5. R2
    ss_res = float(np.sum(errors ** 2))
    ss_tot = float(np.sum((yt - np.mean(yt)) ** 2))
    if ss_tot > 0:
        r2 = float(1.0 - (ss_res / ss_tot))
    else:
        r2 = 1.0 if ss_res == 0.0 else 0.0

    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "wape": round(wape, 4),
        "mase": round(mase, 4),
        "r2": round(r2, 4),
    }
