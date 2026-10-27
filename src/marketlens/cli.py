"""Command-line interface for MarketLens AI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from marketlens.config import get_project_root
from marketlens.datasets.adapters.uci_online_retail_ii import UCIOnlineRetailIIAdapter
from marketlens.datasets.manifests import (
    load_candidate_inventory,
    load_datasets_manifest,
    record_acquired_file,
    save_candidate_inventory,
)
from marketlens.datasets.profiler import TabularDataProfiler
from marketlens.datasets.registry import DatasetRegistry
from marketlens.logging_config import configure_logging, get_logger

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

    parsed = parser.parse_args(args)
    return parsed.func(parsed)


if __name__ == "__main__":
    sys.exit(main())
