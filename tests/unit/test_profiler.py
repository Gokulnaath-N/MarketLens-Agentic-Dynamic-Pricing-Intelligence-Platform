"""Unit tests for tabular data profiler."""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import pytest

from marketlens.datasets.profiler import ProfilerError, TabularDataProfiler


@pytest.fixture
def synthetic_csv(tmp_path: Path) -> Path:
    """Create a temporary synthetic CSV fixture with prices, dates, quantities, and cancellations."""
    file_path = tmp_path / "synthetic_sales.csv"
    data = {
        "Invoice": ["INV001", "INV002", "C_INV003", "INV004", "INV005"],
        "StockCode": ["SKU_A", "SKU_B", "SKU_A", "SKU_C", "SKU_B"],
        "Description": ["Product Alpha", "Product Beta", "Product Alpha", None, "Product Beta"],
        "Quantity": [10, 5, -2, 20, 15],
        "InvoiceDate": [
            "2026-01-01 10:00:00",
            "2026-01-02 11:30:00",
            "2026-01-03 14:15:00",
            "2026-01-04 09:00:00",
            "2026-01-05 16:45:00",
        ],
        "Price": [19.99, 45.50, 19.99, 5.00, 45.50],
    }
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    return file_path


class TestTabularDataProfiler:
    """Tests read-only tabular profiling and heuristics."""

    def test_profile_synthetic_csv(self, synthetic_csv: Path):
        profiler = TabularDataProfiler()
        initial_mtime = synthetic_csv.stat().st_mtime

        report = profiler.profile_file(dataset_id="test_ds", file_path=synthetic_csv)

        # 1. Integrity: Source file was not mutated
        assert synthetic_csv.stat().st_mtime == initial_mtime

        # 2. Dimensions
        assert report.row_count == 5
        assert report.column_count == 6

        # 3. Domain detection
        assert report.detected_target_column == "Quantity"
        assert report.detected_price_column == "Price"
        assert report.detected_time_column == "InvoiceDate"
        assert "Invoice" in report.detected_identifier_columns
        assert "StockCode" in report.detected_identifier_columns

        # 4. Quality issues (negative quantity detected)
        assert any("negative values" in q for q in report.data_quality_issues)

        # 5. Unsupported features identified
        assert any("competitor_prices" in u for u in report.unsupported_fields)
        assert any("customer_reviews" in u for u in report.unsupported_fields)

    def test_unsupported_format_raises_profiler_error(self, tmp_path: Path):
        unsupported = tmp_path / "data.unsupported"
        unsupported.write_text("random bytes", encoding="utf-8")

        profiler = TabularDataProfiler()
        with pytest.raises(ProfilerError, match="Unsupported tabular format"):
            profiler.profile_file(dataset_id="test", file_path=unsupported)

    def test_missing_file_raises_filenotfound(self, tmp_path: Path):
        profiler = TabularDataProfiler()
        with pytest.raises(FileNotFoundError):
            profiler.profile_file(dataset_id="test", file_path=tmp_path / "missing.csv")
