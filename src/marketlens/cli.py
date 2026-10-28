"""Command-line interface for MarketLens AI."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import sys
from pathlib import Path

from marketlens.agents.competitor_monitor import CompetitorMonitorAgent
from marketlens.agents.review_insights import ReviewInsightAgent
from marketlens.agents.schemas import CompetitorObservation, ExtractionMethod, ReviewInputRecord

from marketlens.config import get_project_root, load_yaml_config
from marketlens.experiments.ablation import FeatureAblationRunner
from marketlens.datasets.adapters.uci_online_retail_ii import UCIOnlineRetailIIAdapter
from marketlens.datasets.manifests import (
    load_candidate_inventory,
    load_datasets_manifest,
    record_acquired_file,
    save_candidate_inventory,
)
from marketlens.datasets.profiler import TabularDataProfiler
from marketlens.datasets.registry import DatasetRegistry
from marketlens.data.aggregation import aggregate_to_demand_series
from marketlens.data.canonicalize import canonicalize_uci_transactions
from marketlens.data.cleaning import clean_uci_transactions
from marketlens.data.loaders import load_uci_raw_transactions
from marketlens.data.split import chronological_split
from marketlens.features.temporal import build_temporal_features
from marketlens.forecasting.artifacts import save_evaluation_artifacts, save_processed_datasets
from marketlens.forecasting.evaluate import train_and_evaluate_models
from marketlens.logging_config import configure_logging, get_logger
from marketlens.pricing.optimizer import PricingOptimizer
from marketlens.pricing.scenario import ConstantElasticityDemandAdapter
from marketlens.pricing.schemas import OptimizationObjective, OptimizationRequest

logger = get_logger("marketlens.cli")


def cmd_datasets_discover(args: argparse.Namespace) -> int:
    """Discover candidate datasets, evaluate hard-gates, and persist candidate inventory."""
    registry = DatasetRegistry()
    candidates = registry.list_candidates()
    inventory_path = save_candidate_inventory(candidates)

    print("=" * 80)
    print(f"MARKETLENS AI — DATASET CANDIDATE DISCOVERY ({len(candidates)} candidates evaluated)")
    print("=" * 80)
    for c in candidates:
        status_symbol = "✓ PASSED" if c.hard_gate_status == "passed" else f"✗ {c.hard_gate_status.upper()}"
        print(f"\n[{status_symbol}] {c.name} ({c.dataset_id})")
        print(f"  • Role:             {c.role}")
        print(f"  • Publisher:        {c.publisher}")
        print(f"  • License:          {c.license.license_name}")
        print(f"  • Decision:         {c.decision.upper()} — {c.decision_reason}")
        print(f"  • Suitability:      {c.suitability_score}/100 pts")
        print(f"  • Dimensions:       {json.dumps(c.dimension_scores)}")
        print(f"  • Features:         Qty={c.has_sales_quantity}, Price={c.has_observed_price}, Time={c.has_timestamps}, Reviews={c.has_customer_reviews}, CompPrices={c.has_competitor_prices}")
        print(f"  • Key Limitations:  {'; '.join(c.known_limitations[:2])}")

    print("\n" + "-" * 80)
    print(f"Candidate inventory saved to: {inventory_path.relative_to(get_project_root())}")
    print("-" * 80)
    return 0


def cmd_datasets_status(args: argparse.Namespace) -> int:
    """Show current local dataset acquisition status from manifests and raw storage."""
    manifest = load_datasets_manifest()
    root = get_project_root()
    raw_dir = root / "data" / "raw"

    print("=" * 80)
    print("MARKETLENS AI — LOCAL DATASET ACQUISITION STATUS")
    print("=" * 80)

    if not manifest:
        print("\nNo datasets currently registered in datasets_manifest.json.")
        print("Run 'python -m marketlens.cli datasets download --source uci_online_retail_ii' to acquire data.")
    else:
        for ds_id, prov in manifest.items():
            print(f"\nDataset: {prov.name} ({ds_id})")
            print(f"  • Publisher:    {prov.publisher}")
            print(f"  • License:      {prov.license_name}")
            print(f"  • Acquired At:  {prov.acquired_at_utc}")
            print(f"  • Files ({len(prov.files)}):")
            for f in prov.files:
                size_mb = f.byte_size / (1024 * 1024)
                print(f"    - {f.filename} [{f.detected_format.upper()}] ({size_mb:.2f} MB)")
                print(f"      Path:   {f.file_path}")
                print(f"      SHA256: {f.sha256_hash[:16]}...")
                print(f"      Status: {f.validation_status}")

    return 0


def cmd_datasets_download(args: argparse.Namespace) -> int:
    """Acquire approved dataset using bounded, integrity-checked downloader."""
    registry = DatasetRegistry()
    candidate = registry.get_candidate(args.source)

    if not candidate:
        print(f"Error: Unknown dataset source '{args.source}'.", file=sys.stderr)
        print(f"Registered sources: {[c.dataset_id for c in registry.list_candidates()]}", file=sys.stderr)
        return 1

    if candidate.hard_gate_status != "passed":
        print(f"Cannot acquire dataset '{candidate.dataset_id}': {candidate.hard_gate_reason}", file=sys.stderr)
        return 2

    print(f"Initiating acquisition for '{candidate.name}' (dry-run: {args.dry_run})...")
    adapter = UCIOnlineRetailIIAdapter()
    
    try:
        acquired_files = adapter.acquire(candidate, dry_run=args.dry_run, force=args.force)
        if args.dry_run:
            print("\n[DRY RUN PLAN COMPLETED]")
            print(f"Source URL:          {candidate.download_url}")
            print(f"Target files:        {[f.filename for f in acquired_files]}")
            print(f"License:             {candidate.license.license_name}")
            print("Status:              Ready for acquisition (no files modified).")
            return 0

        # Record files in manifest
        for f in acquired_files:
            record_acquired_file(
                dataset_id=candidate.dataset_id,
                dataset_name=candidate.name,
                publisher=candidate.publisher,
                license_name=candidate.license.license_name,
                license_url=candidate.license.license_url,
                citation=candidate.citation,
                acquired_file=f,
            )

        print(f"\nSuccessfully acquired and verified {len(acquired_files)} files for '{candidate.dataset_id}':")
        for f in acquired_files:
            print(f"  • {f.filename} ({f.byte_size / (1024**2):.2f} MB) | SHA256: {f.sha256_hash[:16]}... | {f.validation_status}")

        return 0

    except Exception as e:
        print(f"Acquisition error: {e}", file=sys.stderr)
        return 3


def cmd_datasets_profile(args: argparse.Namespace) -> int:
    """Run read-only statistical profiling on an acquired tabular dataset."""
    root = get_project_root()
    manifest = load_datasets_manifest()

    if args.source not in manifest:
        print(f"Error: Dataset '{args.source}' has not been acquired yet.", file=sys.stderr)
        print("Run 'python -m marketlens.cli datasets download' first.", file=sys.stderr)
        return 1

    prov = manifest[args.source]
    # Find candidate tabular file (xlsx, xls, or csv)
    tabular_file = next(
        (f for f in prov.files if f.detected_format in ["xlsx", "xls", "csv"] or Path(f.filename).suffix.lower() in [".xlsx", ".xls", ".csv"]),
        None,
    )

    if not tabular_file:
        print(f"Error: No tabular file found in acquired records for '{args.source}'.", file=sys.stderr)
        return 2

    full_path = root / tabular_file.file_path
    print(f"Profiling tabular file: {tabular_file.filename} (sample limit: {args.sample})...")
    profiler = TabularDataProfiler(sample_size=args.sample)

    try:
        report = profiler.profile_file(dataset_id=args.source, file_path=full_path)
        out_path = profiler.save_profile_report(report)

        print("=" * 80)
        print(f"DATA PROFILING SUMMARY: {report.dataset_id}")
        print("=" * 80)
        print(f"Source file:           {report.source_file}")
        print(f"Rows x Columns:        {report.row_count:,} x {report.column_count}")
        print(f"Date Range:            {report.min_timestamp} to {report.max_timestamp}")
        print(f"Duplicate sample rows: {report.duplicate_rows_detected}")
        print(f"Detected Target:       {report.detected_target_column}")
        print(f"Detected Price:        {report.detected_price_column}")
        print(f"Detected Time:         {report.detected_time_column}")
        print(f"Detected Keys:         {report.detected_identifier_columns}")
        print(f"Forecasting Check:     {report.suitability_for_forecasting}")
        print(f"Quality flags ({len(report.data_quality_issues)}):")
        for q in report.data_quality_issues:
            print(f"  ! {q}")
        print(f"Unsupported features:")
        for u in report.unsupported_fields:
            print(f"  - {u}")
        print("-" * 80)
        print(f"Full profile JSON saved to: {out_path.relative_to(root)}")
        return 0

    except Exception as e:
        print(f"Profiling error: {e}", file=sys.stderr)
        return 3


def cmd_forecast_pipeline(args: argparse.Namespace) -> int:
    """Execute end-to-end data processing, feature engineering, and baseline forecasting."""
    root = get_project_root()
    print("=" * 80)
    print("MARKETLENS AI — DATA PROCESSING & BASELINE FORECASTING PIPELINE")
    print("=" * 80)

    try:
        # 1. Load raw data
        raw_df = load_uci_raw_transactions(sample_rows_per_sheet=args.sample_rows)

        # 2. Clean & audit exclusions
        clean_df, audit = clean_uci_transactions(raw_df)

        # 3. Canonicalize
        sales_df, catalog_df = canonicalize_uci_transactions(clean_df)

        # 4. Aggregate to regular demand series
        demand_df = aggregate_to_demand_series(
            canonical_sales=sales_df,
            freq=args.freq,
            min_active_periods=args.min_active,
            top_n_products=args.top_products,
        )

        # 5. Persist processed datasets to Parquet
        saved_paths = save_processed_datasets(sales_df, demand_df)
        print(f"✓ Saved canonical sales to: {saved_paths['sales_observations']}")
        print(f"✓ Saved demand time-series to: {saved_paths['demand_timeseries']}")

        # 6. Feature engineering (leakage-safe)
        features_df = build_temporal_features(
            demand_df=demand_df,
            target_col="units_sold",
            price_col="mean_unit_price",
            time_col="period_start",
            product_id_col="product_id",
            horizon=args.horizon,
        )

        # 7. Chronological splitting
        train_df, val_df, test_df, split_meta = chronological_split(
            features_df,
            time_col="period_start",
            train_ratio=0.70,
            val_ratio=0.15,
            test_ratio=0.15,
        )

        feature_cols = [
            c
            for c in features_df.columns
            if c.startswith("target_lag_")
            or c.startswith("rolling_")
            or c.startswith("price_")
            or c.startswith("cal_")
            or c in ["sin_month", "cos_month"]
        ]

        # 8. Train & Evaluate models
        metrics_df, preds_df, _ = train_and_evaluate_models(
            train_df=train_df,
            test_df=test_df,
            feature_cols=feature_cols,
            target_col="units_sold",
            random_seed=42,
        )

        # 9. Save artifacts and derived manifest
        artifacts = save_evaluation_artifacts(
            metrics_df=metrics_df,
            predictions_df=preds_df,
            split_metadata=split_meta,
            cleaning_audit=audit,
        )

        print("\n" + "=" * 80)
        print("FINAL BASELINE MODEL COMPARISON (Held-Out Test Set):")
        print("=" * 80)
        print(metrics_df.to_string(index=False))
        print("-" * 80)
        print(f"Artifacts successfully saved to: artifacts/")
        print(f"Derived lineage manifest saved to: {artifacts['derived_manifest']}")
        return 0

    except Exception as e:
        print(f"Pipeline error: {e}", file=sys.stderr)
        logger.exception("Forecasting pipeline failed.")
        return 3


def cmd_forecast_ablate(args: argparse.Namespace) -> int:
    """Execute Phase 5 four-way feature ablation study."""
    print("=" * 80)
    print("MARKETLENS AI — PHASE 5 FEATURE ABLATION EXPERIMENTS")
    print("=" * 80)

    try:
        cfg = load_yaml_config(args.config)
        runner = FeatureAblationRunner(config=cfg)
        manifest, comparison_df = runner.run_ablation(
            allow_synthetic_simulation=args.simulate_synthetic,
        )

        print("\n" + "=" * 80)
        print("PHASE 5 ABLATION RESULTS SUMMARY (Held-Out Test Set):")
        print("=" * 80)
        print(comparison_df.to_string(index=False))
        print("-" * 80)
        print(f"Run ID:      {manifest.run_id}")
        print(f"Artifacts:   {runner.tracking_dir}")
        return 0
    except Exception as e:
        print(f"Ablation study error: {e}", file=sys.stderr)
        logger.exception("Ablation study failed.")
        return 1


def cmd_pricing_optimize(args: argparse.Namespace) -> int:
    """Execute constrained pricing optimization for a candidate SKU."""
    print("=" * 80)
    print("MARKETLENS AI — CONSTRAINED PRICING OPTIMIZATION ENGINE")
    print("=" * 80)

    try:
        objective = OptimizationObjective(args.objective.lower())
        request = OptimizationRequest(
            product_id=args.product_id,
            current_price=args.current_price,
            price_min=args.price_min,
            price_max=args.price_max,
            price_step=args.step,
            num_candidates=args.num_candidates,
            objective=objective,
            unit_cost=args.unit_cost,
            min_gross_margin=args.min_margin,
            max_price_change_pct=args.max_change_pct,
            currency=args.currency,
            is_synthetic=args.is_synthetic,
        )

        # Build demand predictor adapter
        # Uses explicit elasticity adapter for scenario pricing
        adapter = ConstantElasticityDemandAdapter(
            base_demand=args.base_demand,
            reference_price=args.current_price,
            elasticity=args.elasticity,
            is_synthetic=args.is_synthetic,
        )

        optimizer = PricingOptimizer(
            tie_breaking_strategy="closest_to_current",
            extrapolation_policy="warn",
        )

        result = optimizer.optimize(
            request=request,
            predictor=adapter,
            support_min=args.support_min,
            support_max=args.support_max,
        )

        print(result.explanation)
        print("-" * 80)
        print(f"Status:                     {result.status.value}")
        print(f"Human Approval Required:    {result.human_approval_required}")
        print(f"Is Synthetic Scenario:      {result.is_synthetic}")
        print("=" * 80)
        return 0

    except Exception as e:
        print(f"Pricing optimization error: {e}", file=sys.stderr)
        logger.exception("Pricing optimization failed.")
        return 4


def cmd_market_review(args: argparse.Namespace) -> int:
    """Analyze single customer review text using rule-based or mock extractor."""
    print("=" * 80)
    print("MARKETLENS AI — CUSTOMER REVIEW INSIGHT AGENT")
    print("=" * 80)
    try:
        agent = ReviewInsightAgent(
            extraction_method=ExtractionMethod(args.method.lower())
        )
        record = ReviewInputRecord(
            review_id=args.review_id,
            product_id=args.product_id,
            review_text=args.text,
            rating=args.rating,
            is_synthetic=args.is_synthetic,
        )
        insight = agent.process_review(record)
        print(f"Review ID:           {insight.review_id}")
        print(f"Product ID:          {insight.product_id}")
        print(f"Sentiment:           {insight.sentiment_label.value.upper()} (score: {insight.sentiment_score:.2f})")
        print(f"Aspects:             {', '.join(insight.aspects) if insight.aspects else 'None'}")
        print(f"Complaint Types:     {', '.join(insight.complaint_categories) if insight.complaint_categories else 'None'}")
        print(f"Praise Types:        {', '.join(insight.praise_categories) if insight.praise_categories else 'None'}")
        print(f"Evidence Excerpt:    {insight.evidence_excerpt or 'None'}")
        print(f"Summary:             {insight.summary}")
        print(f"Method:              {insight.extraction_method.value}")
        print(f"Validation:          {insight.validation_status.value}")
        if insight.warnings:
            print(f"Warnings:            {'; '.join(insight.warnings)}")
        print("=" * 80)
        return 0
    except Exception as e:
        print(f"Review analysis error: {e}", file=sys.stderr)
        return 5


def cmd_market_competitor(args: argparse.Namespace) -> int:
    """Detect deterministic price change metrics between two competitor observations."""
    print("=" * 80)
    print("MARKETLENS AI — COMPETITOR MONITORING AGENT")
    print("=" * 80)
    try:
        now = datetime.now(timezone.utc)
        prev = CompetitorObservation(
            observation_id="cli_prev",
            product_id=args.product_id,
            competitor_id=args.competitor_id,
            observed_price=args.prev_price,
            currency=args.currency,
            observed_at=now,
            is_synthetic=args.is_synthetic,
        )
        curr = CompetitorObservation(
            observation_id="cli_curr",
            product_id=args.product_id,
            competitor_id=args.competitor_id,
            observed_price=args.curr_price,
            currency=args.currency,
            observed_at=now,
            is_synthetic=args.is_synthetic,
        )
        agent = CompetitorMonitorAgent(price_change_threshold_pct=args.threshold)
        evt = agent.detect_change(prev, curr)

        print(f"Competitor ID:       {evt.competitor_id}")
        print(f"Product ID:          {evt.product_id}")
        print(f"Price Movement:      {evt.previous_price:.2f} -> {evt.current_price:.2f} {evt.currency}")
        print(f"Absolute Change:     {evt.absolute_change:+.2f} {evt.currency}")
        print(f"Percentage Change:   {evt.percentage_change:+.1f}% ({evt.direction.value})")
        print(f"Threshold Exceeded:  {evt.threshold_exceeded} (limit: {args.threshold}%)")
        print(f"Stale Observation:   {evt.is_stale}")
        print(f"Synthetic Data:      {evt.is_synthetic}")
        print("=" * 80)
        return 0
    except Exception as e:
        print(f"Competitor monitor error: {e}", file=sys.stderr)
        return 6


def main(args: list[str] | None = None) -> int:
    """CLI entry point for MarketLens AI."""
    configure_logging()
    parser = argparse.ArgumentParser(
        prog="marketlens",
        description="MarketLens AI — Agentic Dynamic Pricing Intelligence Platform CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # datasets command group
    datasets_parser = subparsers.add_parser("datasets", help="Dataset discovery, acquisition, and profiling")
    datasets_sub = datasets_parser.add_subparsers(dest="subcommand", required=True)

    # datasets discover
    discover_parser = datasets_sub.add_parser("discover", help="Discover candidate datasets and evaluate licenses")
    discover_parser.set_defaults(func=cmd_datasets_discover)

    # datasets status
    status_parser = datasets_sub.add_parser("status", help="Show local acquisition status")
    status_parser.set_defaults(func=cmd_datasets_status)

    # datasets download
    download_parser = datasets_sub.add_parser("download", help="Download approved dataset")
    download_parser.add_argument("--source", required=True, help="Dataset identifier (e.g. uci_online_retail_ii)")
    download_parser.add_argument("--dry-run", action="store_true", help="Plan acquisition without downloading")
    download_parser.add_argument("--force", action="store_true", help="Force re-download even if already present")
    download_parser.set_defaults(func=cmd_datasets_download)

    # datasets profile
    profile_parser = datasets_sub.add_parser("profile", help="Profile an acquired tabular file")
    profile_parser.add_argument("--source", required=True, help="Dataset identifier (e.g. uci_online_retail_ii)")
    profile_parser.add_argument("--sample", type=int, default=100000, help="Max rows to profile (default: 100,000 for memory safety)")
    profile_parser.set_defaults(func=cmd_datasets_profile)

    # forecast command group
    forecast_parser = subparsers.add_parser("forecast", help="Forecasting pipelines, training, and evaluation")
    forecast_sub = forecast_parser.add_subparsers(dest="subcommand", required=True)

    # forecast pipeline
    pipeline_parser = forecast_sub.add_parser("pipeline", help="Run end-to-end data processing, feature engineering, and model evaluation")
    pipeline_parser.add_argument("--sample-rows", type=int, default=50000, help="Sample rows per sheet (default: 50,000 for fast local execution; 0 for all)")
    pipeline_parser.add_argument("--freq", default="W-MON", help="Time aggregation grain (default: 'W-MON' for weekly)")
    pipeline_parser.add_argument("--top-products", type=int, default=50, help="Number of top volume products to model (default: 50)")
    pipeline_parser.add_argument("--min-active", type=int, default=10, help="Minimum active periods to keep a product (default: 10)")
    pipeline_parser.add_argument("--horizon", type=int, default=1, help="Forecast horizon steps ahead (default: 1)")
    pipeline_parser.set_defaults(func=cmd_forecast_pipeline)

    # forecast ablate
    ablate_parser = forecast_sub.add_parser("ablate", help="Run Phase 5 4-way feature ablation study (E0-E3)")
    ablate_parser.add_argument("--config", default="phase5_experiments.yaml", help="Path to experiment YAML configuration")
    ablate_parser.add_argument("--simulate-synthetic", action="store_true", help="Run simulation with synthetic fixtures to test E1-E3")
    ablate_parser.set_defaults(func=cmd_forecast_ablate)

    # pricing command group
    pricing_parser = subparsers.add_parser("pricing", help="Price optimization and scenario evaluation")
    pricing_sub = pricing_parser.add_subparsers(dest="subcommand", required=True)

    # pricing optimize
    opt_parser = pricing_sub.add_parser("optimize", help="Evaluate candidate prices against constraints and objectives")
    opt_parser.add_argument("--product-id", required=True, help="Product SKU or canonical identifier")
    opt_parser.add_argument("--current-price", type=float, required=True, help="Current selling price")
    opt_parser.add_argument("--price-min", type=float, required=True, help="Minimum allowable price bound")
    opt_parser.add_argument("--price-max", type=float, required=True, help="Maximum allowable price bound")
    opt_parser.add_argument("--step", type=float, default=None, help="Discrete price grid increment")
    opt_parser.add_argument("--num-candidates", type=int, default=21, help="Number of candidate points if step is omitted")
    opt_parser.add_argument("--objective", default="revenue", choices=["revenue", "profit"], help="Target objective")
    opt_parser.add_argument("--unit-cost", type=float, default=None, help="Unit cost (COGS). Required if objective is profit")
    opt_parser.add_argument("--min-margin", type=float, default=None, help="Minimum gross margin proportion (e.g. 0.15)")
    opt_parser.add_argument("--max-change-pct", type=float, default=None, help="Maximum price movement proportion (e.g. 0.20)")
    opt_parser.add_argument("--currency", default="GBP", help="Currency code (default: GBP)")
    opt_parser.add_argument("--elasticity", type=float, default=-1.5, help="Demand price elasticity parameter (default: -1.5)")
    opt_parser.add_argument("--base-demand", type=float, default=100.0, help="Baseline expected demand at current price")
    opt_parser.add_argument("--support-min", type=float, default=None, help="Historical minimum observed training price")
    opt_parser.add_argument("--support-max", type=float, default=None, help="Historical maximum observed training price")
    opt_parser.add_argument("--is-synthetic", action="store_true", help="Explicitly mark inputs or costs as synthetic scenario")
    opt_parser.set_defaults(func=cmd_pricing_optimize)

    # market intelligence command group
    market_parser = subparsers.add_parser("market", help="Market intelligence workflows (reviews, competitors, signals)")
    market_sub = market_parser.add_subparsers(dest="subcommand", required=True)

    # market review
    rev_parser = market_sub.add_parser("review", help="Analyze customer review perception")
    rev_parser.add_argument("--review-id", default="cli_rev_1", help="Review identifier")
    rev_parser.add_argument("--product-id", required=True, help="Product identifier")
    rev_parser.add_argument("--text", required=True, help="Customer review text to evaluate")
    rev_parser.add_argument("--rating", type=float, default=None, help="Rating score (1.0 to 5.0)")
    rev_parser.add_argument("--method", default="rule_based", choices=["rule_based", "mock"], help="Extraction method")
    rev_parser.add_argument("--is-synthetic", action="store_true", help="Mark as synthetic test record")
    rev_parser.set_defaults(func=cmd_market_review)

    # market competitor
    comp_parser = market_sub.add_parser("competitor", help="Detect competitor price movement")
    comp_parser.add_argument("--product-id", required=True, help="Product identifier")
    comp_parser.add_argument("--competitor-id", required=True, help="Competitor identifier")
    comp_parser.add_argument("--prev-price", type=float, required=True, help="Prior observed price")
    comp_parser.add_argument("--curr-price", type=float, required=True, help="Current observed price")
    comp_parser.add_argument("--currency", default="GBP", help="Currency code")
    comp_parser.add_argument("--threshold", type=float, default=5.0, help="Percentage alert threshold")
    comp_parser.add_argument("--is-synthetic", action="store_true", help="Mark as synthetic test record")
    comp_parser.set_defaults(func=cmd_market_competitor)

    parsed = parser.parse_args(args)
    return parsed.func(parsed)


if __name__ == "__main__":
    sys.exit(main())
