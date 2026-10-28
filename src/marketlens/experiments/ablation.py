"""Master feature ablation runner for Phase 5 hybrid model evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from marketlens.config import get_project_root, load_yaml_config
from marketlens.data.split import chronological_split
from marketlens.experiments.schemas import (
    AblationRunManifest,
    ExperimentStatus,
    ExperimentVariant,
    MetricResult,
    VariantRunResult,
)
from marketlens.features.market_signals import merge_market_signals
from marketlens.features.temporal import build_temporal_features
from marketlens.forecasting.baselines import (
    BaseForecaster,
    MovingAverageForecaster,
    NaiveLastObservedForecaster,
    RandomForestDemandForecaster,
    RidgeRegressionForecaster,
)
from marketlens.forecasting.metrics import compute_forecasting_metrics
from marketlens.logging_config import get_logger
from marketlens.pricing.optimizer import PricingOptimizer
from marketlens.pricing.scenario import DirectModelPredictor
from marketlens.pricing.schemas import OptimizationObjective, OptimizationRequest

logger = get_logger("marketlens.experiments.ablation")


class FeatureAblationRunner:
    """Orchestrates four-way feature ablation (E0-E3) under identical chronological evaluation."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or load_yaml_config("phase5_experiments.yaml")
        self.root_dir = get_project_root()
        
        exp_cfg = self.config.get("experiment", {})
        self.run_id = f"ablation_{exp_cfg.get('name', 'phase5')}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
        self.tracking_dir = self.root_dir / exp_cfg.get("tracking_dir", "artifacts/phase5")
        self.tracking_dir.mkdir(parents=True, exist_ok=True)

        self.random_seed = int(exp_cfg.get("random_seed", 42))
        self.data_cfg = self.config.get("data", {})
        self.target_col = self.data_cfg.get("target_column", "units_sold")
        self.time_col = self.data_cfg.get("time_column", "period_start")
        self.product_id_col = self.data_cfg.get("product_id_column", "product_id")
        self.price_col = self.data_cfg.get("price_column", "mean_unit_price")

        # Feature groups
        fg_cfg = self.config.get("feature_groups", {})
        self.baseline_features = fg_cfg.get("baseline", [])
        self.review_features = fg_cfg.get("review_intelligence", [])
        self.competitor_features = fg_cfg.get("competitor_intelligence", [])

        # Model configuration
        model_cfg = self.config.get("models", {})
        self.primary_model_name = model_cfg.get("primary_ablation_model", "random_forest")

    def _instantiate_model(self, model_name: str) -> BaseForecaster:
        """Create model instance based on configuration."""
        if model_name == "naive_last_observed":
            return NaiveLastObservedForecaster(lag_col="target_lag_1")
        elif model_name == "moving_average_4w":
            return MovingAverageForecaster(rolling_col="rolling_mean_4")
        elif model_name == "ridge_regression":
            return RidgeRegressionForecaster(alpha=10.0)
        elif model_name == "random_forest":
            return RandomForestDemandForecaster(
                n_estimators=100,
                max_depth=8,
                random_state=self.random_seed,
            )
        raise ValueError(f"Unknown model name: {model_name}")

    def run_ablation(
        self,
        df: Optional[pd.DataFrame] = None,
        reviews: Optional[List[Any]] = None,
        competitor_observations: Optional[List[Any]] = None,
        competitor_events: Optional[List[Any]] = None,
        allow_synthetic_simulation: bool = False,
    ) -> Tuple[AblationRunManifest, pd.DataFrame]:
        """Execute the four-way feature ablation study.

        Args:
            df: Optional pre-loaded demand timeseries DataFrame.
            reviews: Optional list of review perception signals.
            competitor_observations: Optional list of competitor price observations.
            competitor_events: Optional list of competitor price change events.
            allow_synthetic_simulation: If True, evaluates simulated synthetic signals for test verification.

        Returns:
            Tuple of (AblationRunManifest, comparison_metrics_df).
        """
        logger.info(f"Starting Phase 5 Feature Ablation Study (Run ID: {self.run_id})...")

        # 1. Load Data
        if df is None:
            data_path = self.root_dir / self.data_cfg.get("primary_dataset", "data/processed/demand_timeseries.parquet")
            if not data_path.exists():
                raise FileNotFoundError(f"Primary demand timeseries dataset not found at {data_path}")
            df = pd.read_parquet(data_path)

        df = df.copy()
        df[self.time_col] = pd.to_datetime(df[self.time_col])

        # 2. Ensure baseline temporal features exist
        if "target_lag_1" not in df.columns:
            logger.info("Building baseline temporal and price features...")
            df = build_temporal_features(
                demand_df=df,
                target_col=self.target_col,
                price_col=self.price_col,
                time_col=self.time_col,
                product_id_col=self.product_id_col,
            )

        # 3. Check Real External Data Availability
        has_real_reviews = reviews is not None and len(reviews) > 0 and not any(getattr(r, "is_synthetic", False) for r in reviews)
        has_real_competitors = competitor_observations is not None and len(competitor_observations) > 0 and not any(getattr(o, "is_synthetic", False) for o in competitor_observations)

        # Check if synthetic signals provided for simulation
        has_simulated_signals = (reviews is not None or competitor_observations is not None) and allow_synthetic_simulation

        if has_simulated_signals:
            logger.info("Merging simulated market signals into demand DataFrame for verification...")
            df = merge_market_signals(
                demand_df=df,
                reviews=reviews,
                competitor_observations=competitor_observations,
                competitor_events=competitor_events,
                time_col=self.time_col,
                product_id_col=self.product_id_col,
            )
        elif not has_real_reviews and not has_real_competitors:
            logger.warning(
                "Real customer review and competitor price feeds are absent from primary dataset. "
                "E1, E2, E3 will be designated NOT_RUN (MISSING_REAL_DATA) in accordance with Project Principle 1."
            )

        # 4. Chronological Holdout Split (70% train / 15% val / 15% test)
        train_df, val_df, test_df, _ = chronological_split(
            df=df,
            time_col=self.time_col,
            train_ratio=0.70,
            val_ratio=0.15,
            test_ratio=0.15,
        )

        train_range = [str(train_df[self.time_col].min()), str(train_df[self.time_col].max())]
        val_range = [str(val_df[self.time_col].min()), str(val_df[self.time_col].max())]
        test_range = [str(test_df[self.time_col].min()), str(test_df[self.time_col].max())]
        shared_test_rows = len(test_df)

        logger.info(
            f"Chronological Split: Train={len(train_df):,} periods ({train_range[0]} to {train_range[1]}), "
            f"Test={len(test_df):,} periods ({test_range[0]} to {test_range[1]})."
        )

        # 5. Define Feature Sets for Variants
        variant_features: Dict[ExperimentVariant, List[str]] = {
            ExperimentVariant.E0: [f for f in self.baseline_features if f in df.columns],
            ExperimentVariant.E1: [f for f in (self.baseline_features + self.review_features) if f in df.columns],
            ExperimentVariant.E2: [f for f in (self.baseline_features + self.competitor_features) if f in df.columns],
            ExperimentVariant.E3: [f for f in (self.baseline_features + self.review_features + self.competitor_features) if f in df.columns],
        }

        # 6. Execute Ablation Variants
        variant_results: Dict[str, VariantRunResult] = {}
        e0_metrics: Optional[MetricResult] = None
        metrics_table_rows = []
        all_predictions = []

        for var_enum in [ExperimentVariant.E0, ExperimentVariant.E1, ExperimentVariant.E2, ExperimentVariant.E3]:
            var_key = var_enum.value
            feature_list = variant_features[var_enum]

            # Determine eligibility
            if var_enum == ExperimentVariant.E0:
                is_runnable = True
                status = ExperimentStatus.COMPLETED
                reason = "Evaluated on canonical baseline sales, price, and calendar features."
            elif has_simulated_signals:
                is_runnable = True
                status = ExperimentStatus.SYNTHETIC_SIMULATED
                reason = "Evaluated using verified synthetic market signal fixtures."
            elif var_enum == ExperimentVariant.E1 and not has_real_reviews:
                is_runnable = False
                status = ExperimentStatus.NOT_RUN
                reason = "Not run on real data: primary dataset uci_online_retail_ii has no customer review text."
            elif var_enum == ExperimentVariant.E2 and not has_real_competitors:
                is_runnable = False
                status = ExperimentStatus.NOT_RUN
                reason = "Not run on real data: primary dataset uci_online_retail_ii has no competitor price observations."
            elif var_enum == ExperimentVariant.E3 and (not has_real_reviews or not has_real_competitors):
                is_runnable = False
                status = ExperimentStatus.NOT_RUN
                reason = "Not run on real data: missing real review text and competitor price feeds."
            else:
                is_runnable = True
                status = ExperimentStatus.COMPLETED
                reason = "Evaluated on validated market signals."

            if not is_runnable:
                logger.info(f"Variant '{var_key}' designated {status.value}: {reason}")
                variant_results[var_key] = VariantRunResult(
                    variant_id=var_enum,
                    status=status,
                    status_reason=reason,
                    feature_count=len(feature_list),
                    feature_names=feature_list,
                    model_name=self.primary_model_name,
                    test_rows=0,
                    metrics=None,
                    is_synthetic=False,
                )
                metrics_table_rows.append({
                    "variant": var_key,
                    "status": status.value,
                    "feature_count": len(feature_list),
                    "mae": None,
                    "rmse": None,
                    "wape": None,
                    "mase": None,
                    "r2": None,
                    "delta_mae": None,
                    "pct_delta_mae": None,
                    "notes": reason,
                })
                continue

            # Run Model Training and Evaluation
            logger.info(f"Training and evaluating variant '{var_key}' with {len(feature_list)} features...")
            model = self._instantiate_model(self.primary_model_name)
            model.fit(train_df, target_col=self.target_col, feature_cols=feature_list)

            preds = model.predict(test_df, feature_cols=feature_list)
            y_test = test_df[self.target_col].values
            y_train = train_df[self.target_col].values

            raw_metrics = compute_forecasting_metrics(y_true=y_test, y_pred=preds, y_train=y_train)

            # Store predictions
            pred_df = pd.DataFrame({
                "product_id": test_df[self.product_id_col].values,
                "period_start": test_df[self.time_col].values,
                "actual_units": y_test,
                "predicted_units": preds,
                "variant": var_key,
                "model_name": self.primary_model_name,
            })
            all_predictions.append(pred_df)

            # Compute deltas against E0
            delta_mae = None
            delta_rmse = None
            delta_wape = None
            pct_delta_mae = None
            pct_delta_rmse = None

            if var_enum == ExperimentVariant.E0:
                e0_metrics = MetricResult(**raw_metrics)
            elif e0_metrics is not None:
                delta_mae = round(raw_metrics["mae"] - e0_metrics.mae, 4)
                delta_rmse = round(raw_metrics["rmse"] - e0_metrics.rmse, 4)
                delta_wape = round(raw_metrics["wape"] - e0_metrics.wape, 4)
                if e0_metrics.mae > 0:
                    pct_delta_mae = round((delta_mae / e0_metrics.mae) * 100.0, 2)
                if e0_metrics.rmse > 0:
                    pct_delta_rmse = round((delta_rmse / e0_metrics.rmse) * 100.0, 2)

            metric_result = MetricResult(
                mae=raw_metrics["mae"],
                rmse=raw_metrics["rmse"],
                wape=raw_metrics["wape"],
                mase=raw_metrics["mase"],
                r2=raw_metrics["r2"],
                delta_mae=delta_mae,
                delta_rmse=delta_rmse,
                delta_wape=delta_wape,
                pct_delta_mae=pct_delta_mae,
                pct_delta_rmse=pct_delta_rmse,
            )

            # 7. Pricing Evaluation for this variant
            pricing_rec = self._evaluate_pricing_impact(model, test_df, feature_list)

            variant_results[var_key] = VariantRunResult(
                variant_id=var_enum,
                status=status,
                status_reason=reason,
                feature_count=len(feature_list),
                feature_names=feature_list,
                model_name=self.primary_model_name,
                test_rows=len(test_df),
                metrics=metric_result,
                pricing_recommendation=pricing_rec,
                is_synthetic=has_simulated_signals,
            )

            metrics_table_rows.append({
                "variant": var_key,
                "status": status.value,
                "feature_count": len(feature_list),
                "mae": raw_metrics["mae"],
                "rmse": raw_metrics["rmse"],
                "wape": raw_metrics["wape"],
                "mase": raw_metrics["mase"],
                "r2": raw_metrics["r2"],
                "delta_mae": delta_mae,
                "pct_delta_mae": pct_delta_mae,
                "notes": reason,
            })

        # 8. Manifest Construction & Serialization
        comparison_df = pd.DataFrame(metrics_table_rows)
        manifest = AblationRunManifest(
            run_id=self.run_id,
            primary_dataset=self.data_cfg.get("primary_dataset", "demand_timeseries.parquet"),
            target_column=self.target_col,
            forecast_horizon=int(self.data_cfg.get("forecast_horizon", 1)),
            train_range=train_range,
            val_range=val_range,
            test_range=test_range,
            shared_cohort_test_rows=shared_test_rows,
            variant_results=variant_results,
            summary_notes=[
                "E0 evaluated on real historical transactions.",
                "E1-E3 designated NOT_RUN on real data due to absence of customer reviews and competitor feeds in UCI Online Retail II.",
                "All metric deltas signed: negative delta represents forecast accuracy improvement.",
            ],
        )

        # Save artifacts
        self._save_artifacts(manifest, comparison_df, all_predictions)
        return manifest, comparison_df

    def _evaluate_pricing_impact(
        self,
        model: BaseForecaster,
        test_df: pd.DataFrame,
        feature_list: List[str],
    ) -> Optional[Dict[str, Any]]:
        """Evaluate pricing recommendation for a representative product under the model's demand function."""
        try:
            sample_product = test_df[self.product_id_col].iloc[0]
            prod_rows = test_df[test_df[self.product_id_col] == sample_product]
            if prod_rows.empty:
                return None

            latest_row = prod_rows.iloc[-1].to_dict()
            curr_price = float(latest_row.get(self.price_col, 2.50))
            if curr_price <= 0:
                curr_price = 2.50

            request = OptimizationRequest(
                product_id=str(sample_product),
                current_price=curr_price,
                price_min=round(curr_price * 0.75, 2),
                price_max=round(curr_price * 1.25, 2),
                price_step=round(curr_price * 0.05, 2),
                objective=OptimizationObjective.REVENUE,
                max_price_change_pct=0.25,
                demand_context=latest_row,
                is_synthetic=False,
            )

            predictor = DirectModelPredictor(model=model, price_col=self.price_col)
            optimizer = PricingOptimizer(enforce_price_responsiveness=False)

            result = optimizer.optimize(
                request=request,
                predictor=predictor,
                feature_cols=feature_list,
                support_min=curr_price * 0.5,
                support_max=curr_price * 2.0,
            )

            return {
                "product_id": sample_product,
                "current_price": curr_price,
                "recommended_price": result.recommended_price,
                "expected_revenue": result.expected_revenue,
                "status": result.status.value,
                "warnings": result.warnings,
            }
        except Exception as e:
            logger.warning(f"Pricing impact evaluation skipped: {e}")
            return None

    def _save_artifacts(
        self,
        manifest: AblationRunManifest,
        comparison_df: pd.DataFrame,
        prediction_frames: List[pd.DataFrame],
    ) -> None:
        """Persist structured metrics, predictions, and manifests into artifacts directory."""
        # Save metrics CSV & JSON
        csv_path = self.tracking_dir / "ablation_metrics.csv"
        json_path = self.tracking_dir / "ablation_metrics.json"
        comparison_df.to_csv(csv_path, index=False)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(comparison_df.to_dict(orient="records"), f, indent=2)

        # Save run manifest JSON
        manifest_path = self.tracking_dir / "ablation_run_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest.model_dump(mode="json"), f, indent=2)

        # Save predictions Parquet
        if prediction_frames:
            full_preds = pd.concat(prediction_frames, ignore_index=True)
            pred_path = self.tracking_dir / "ablation_predictions.parquet"
            full_preds.to_parquet(pred_path, index=False)

        logger.info(f"Saved Phase 5 ablation artifacts to '{self.tracking_dir}'.")
