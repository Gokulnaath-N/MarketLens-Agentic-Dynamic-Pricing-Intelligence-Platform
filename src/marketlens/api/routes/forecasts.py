"""Demand forecasting endpoints."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
import pandas as pd

from marketlens.api.schemas import (
    ForecastModelListResponse,
    LiveForecastRequest,
    LiveForecastResponse,
    ModelMetricItem,
)
from marketlens.config import get_project_root
from marketlens.pricing.scenario import ConstantElasticityDemandAdapter

router = APIRouter(prefix="/forecasts", tags=["Forecasting"])


@router.get("/models", response_model=ForecastModelListResponse)
def get_forecasting_models() -> ForecastModelListResponse:
    """Retrieve available forecasting models, baseline test metrics, and test sample predictions."""
    root = get_project_root()
    cmp_file = root / "artifacts" / "model_comparison.json"
    preds_file = root / "artifacts" / "test_predictions.parquet"

    metrics_list: List[ModelMetricItem] = []
    models: List[str] = ["NaivePersistence", "HistoricalMean", "ElasticityModel", "XGBoostRegressor"]
    artifacts_exist = cmp_file.is_file()

    if artifacts_exist:
        try:
            with open(cmp_file, "r", encoding="utf-8") as f:
                cmp_data = json.load(f)
            # cmp_data is typically a list of records or dict of model -> metrics
            if isinstance(cmp_data, list):
                for row in cmp_data:
                    metrics_list.append(
                        ModelMetricItem(
                            model_name=row.get("model", row.get("model_name", "unknown")),
                            mae=float(row.get("mae", 0.0)),
                            rmse=float(row.get("rmse", 0.0)),
                            wape=float(row.get("wape", 0.0)),
                            r2=float(row.get("r2", 0.0)),
                            evaluation_split="test",
                        )
                    )
            elif isinstance(cmp_data, dict):
                for m_name, vals in cmp_data.items():
                    if isinstance(vals, dict):
                        metrics_list.append(
                            ModelMetricItem(
                                model_name=m_name,
                                mae=float(vals.get("mae", 0.0)),
                                rmse=float(vals.get("rmse", 0.0)),
                                wape=float(vals.get("wape", 0.0)),
                                r2=float(vals.get("r2", 0.0)),
                                evaluation_split="test",
                            )
                        )
        except Exception:
            pass

    # Sample preview of actual vs predicted
    preview: List[Dict[str, Any]] = []
    if preds_file.is_file():
        try:
            preds_df = pd.read_parquet(preds_file)
            # Pick first 20 records
            sample = preds_df.head(20).copy()
            # Convert timestamp to string if present
            for c in sample.columns:
                if pd.api.types.is_datetime64_any_dtype(sample[c]):
                    sample[c] = sample[c].dt.strftime("%Y-%m-%d")
            preview = sample.to_dict(orient="records")
        except Exception:
            pass

    return ForecastModelListResponse(
        models=models,
        target_column="units_sold",
        frequency="W-MON",
        evaluation_artifacts_exist=artifacts_exist,
        metrics=metrics_list,
        predictions_preview=preview,
    )


@router.post("", response_model=LiveForecastResponse)
def compute_live_forecast(req: LiveForecastRequest) -> LiveForecastResponse:
    """Compute on-demand demand forecast for a candidate price."""
    adapter = ConstantElasticityDemandAdapter(
        base_demand=req.base_demand,
        reference_price=req.reference_price,
        elasticity=req.elasticity,
        is_synthetic=False,
    )

    df = pd.DataFrame([{"candidate_price": req.candidate_price}])
    demand_arr = adapter.predict(df, ["candidate_price"])
    demand = float(demand_arr[0])

    revenue = round(req.candidate_price * demand, 2)

    explanation = (
        f"Demand predicted at {demand:.1f} units for SKU {req.product_id} at price {req.candidate_price:.2f}. "
        f"Assumed elasticity: {req.elasticity:.2f} relative to reference price {req.reference_price:.2f}."
    )

    return LiveForecastResponse(
        product_id=req.product_id,
        candidate_price=req.candidate_price,
        predicted_demand=round(demand, 2),
        expected_revenue=revenue,
        horizon_weeks=req.horizon_weeks,
        model_type="ConstantElasticityDemandAdapter",
        is_synthetic=False,
        explanation=explanation,
    )
