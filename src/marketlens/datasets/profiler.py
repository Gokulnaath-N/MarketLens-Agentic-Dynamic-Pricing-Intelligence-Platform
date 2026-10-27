"""Read-only data profiling for acquired tabular datasets (CSV and Excel)."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any, List, Optional
import pandas as pd

from marketlens.config import get_project_root
from marketlens.datasets.models import ColumnProfile, DataProfileReport


class ProfilerError(Exception):
    """Raised when tabular data cannot be profiled."""

    pass


class TabularDataProfiler:
    """Performs memory-conscious, read-only statistical profiling on tabular files."""

    def __init__(self, sample_size: Optional[int] = None):
        self.sample_size = sample_size

    def profile_file(
        self,
        dataset_id: str,
        file_path: str | Path,
        sheet_name: str | int | None = 0,
    ) -> DataProfileReport:
        """Profile a CSV or Excel file and return a structured DataProfileReport.

        Args:
            dataset_id: Identifier of the dataset.
            file_path: Absolute or project-relative Path to the tabular file.
            sheet_name: For Excel files, sheet index or name (defaults to first sheet).

        Returns:
            DataProfileReport containing schema, statistics, and quality flags.
        """
        root = get_project_root()
        path = Path(file_path)
        if not path.is_absolute():
            path = (root / path).resolve()

        if not path.is_file():
            raise FileNotFoundError(f"File to profile does not exist: {path}")

        ext = path.suffix.lower()
        try:
            if ext in [".csv", ".txt", ".tsv"]:
                df = pd.read_csv(path, nrows=self.sample_size, low_memory=False)
            elif ext in [".xlsx", ".xls"]:
                df = pd.read_excel(path, sheet_name=sheet_name, nrows=self.sample_size)
            else:
                raise ProfilerError(f"Unsupported tabular format for profiling: '{ext}'")
        except Exception as e:
            raise ProfilerError(f"Failed to load file '{path.name}' for profiling: {e}") from e

        row_count, col_count = df.shape
        now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Profiling column-by-column
        columns: list[ColumnProfile] = []
        date_cols: list[str] = []
        numeric_cols: list[str] = []
        detected_id_cols: list[str] = []
        detected_target: Optional[str] = None
        detected_price: Optional[str] = None
        detected_time: Optional[str] = None
        quality_issues: list[str] = []

        for col_name in df.columns:
            series = df[col_name]
            total_cnt = len(series)
            missing_cnt = int(series.isna().sum())
            missing_pct = round((missing_cnt / total_cnt) * 100.0, 2) if total_cnt > 0 else 0.0
            distinct_cnt = int(series.nunique(dropna=True))

            # Inferred type check
            inferred_type = str(series.dtype)
            min_val = None
            max_val = None
            median_val = None

            # Sample values (up to 5 non-null)
            non_null = series.dropna()
            samples = [str(x)[:50] for x in non_null.head(5).tolist()]

            # Date identification
            col_lower = str(col_name).lower()
            if "date" in col_lower or "time" in col_lower or pd.api.types.is_datetime64_any_dtype(series):
                try:
                    dt_series = pd.to_datetime(series, errors="coerce")
                    valid_dts = dt_series.dropna()
                    if len(valid_dts) > 0:
                        min_val = valid_dts.min().isoformat()
                        max_val = valid_dts.max().isoformat()
                        inferred_type = "datetime"
                        date_cols.append(str(col_name))
                        if not detected_time:
                            detected_time = str(col_name)
                except Exception:
                    pass

            # Numeric identification
            if pd.api.types.is_numeric_dtype(series) and inferred_type != "datetime":
                numeric_cols.append(str(col_name))
                if len(non_null) > 0:
                    min_val = float(non_null.min())
                    max_val = float(non_null.max())
                    median_val = float(non_null.median())

                    # Negative checks for price or quantity
                    if "quant" in col_lower and min_val < 0:
                        quality_issues.append(
                            f"Column '{col_name}' has negative values (min: {min_val}), indicating cancellations or returns."
                        )
                    if "price" in col_lower and min_val <= 0:
                        quality_issues.append(
                            f"Column '{col_name}' contains zero or negative values (min: {min_val})."
                        )

            # Domain role heuristics
            if any(term in col_lower for term in ["quantity", "qty", "units_sold"]):
                detected_target = str(col_name)
            if any(term in col_lower for term in ["price", "unit_price", "amount"]):
                detected_price = str(col_name)
            if any(term in col_lower for term in ["stockcode", "item_id", "product_id", "sku", "invoice"]):
                detected_id_cols.append(str(col_name))

            columns.append(
                ColumnProfile(
                    name=str(col_name),
                    inferred_type=inferred_type,
                    total_count=total_cnt,
                    missing_count=missing_cnt,
                    missing_pct=missing_pct,
                    distinct_count=distinct_cnt,
                    min_value=min_val,
                    max_value=max_val,
                    median_value=median_val,
                    sample_values=samples,
                )
            )

        # Duplicate row check (on first 50,000 rows to avoid memory exhaustion)
        dup_count = int(df.head(50000).duplicated().sum())

        # Time range
        min_ts = None
        max_ts = None
        if detected_time:
            dt_s = pd.to_datetime(df[detected_time], errors="coerce").dropna()
            if len(dt_s) > 0:
                min_ts = dt_s.min().isoformat()
                max_ts = dt_s.max().isoformat()

        # Forecasting suitability
        suitability = (
            "Suitable for historical demand forecasting baseline after filtering cancellations "
            "and aggregating to product-day/week grain."
            if detected_target and detected_time and len(detected_id_cols) > 0
            else "Limited suitability: missing required key entity or timestamp columns."
        )

        unsupported = [
            "competitor_prices (not present in raw transaction records)",
            "customer_reviews_and_ratings (no review text or sentiment scores)",
            "unit_costs (wholesale cost of goods not supplied)",
            "inventory_stockouts (inventory levels not reported)",
        ]

        try:
            source_file_str = str(path.relative_to(root)).replace("\\", "/")
        except ValueError:
            source_file_str = str(path).replace("\\", "/")

        return DataProfileReport(
            dataset_id=dataset_id,
            source_file=source_file_str,
            profiled_at_utc=now_utc,
            row_count=row_count,
            column_count=col_count,
            columns=columns,
            min_timestamp=min_ts,
            max_timestamp=max_ts,
            duplicate_rows_detected=dup_count,
            detected_identifier_columns=detected_id_cols,
            detected_target_column=detected_target,
            detected_price_column=detected_price,
            detected_time_column=detected_time,
            data_quality_issues=quality_issues,
            suitability_for_forecasting=suitability,
            unsupported_fields=unsupported,
        )

    def save_profile_report(self, report: DataProfileReport, output_path: Optional[Path] = None) -> Path:
        """Save profile report JSON to data/manifests/profiles/<dataset_id>_profile.json."""
        root = get_project_root()
        dest = output_path or (root / "data" / "manifests" / "profiles" / f"{report.dataset_id}_profile.json")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        return dest
