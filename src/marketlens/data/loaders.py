"""Raw dataset loader utilities for tabular and spreadsheet sources."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional
import pandas as pd

from marketlens.config import get_project_root
from marketlens.logging_config import get_logger

logger = get_logger("marketlens.data.loaders")


def load_uci_raw_transactions(
    file_path: Optional[str | Path] = None,
    sheets: Optional[List[str]] = None,
    sample_rows_per_sheet: Optional[int] = None,
) -> pd.DataFrame:
    """Load raw transaction records from the UCI Online Retail II Excel workbook.

    Args:
        file_path: Path to online_retail_II.xlsx (defaults to data/raw/uci_online_retail_ii/online_retail_II.xlsx).
        sheets: List of sheet names to load. Defaults to both ['Year 2009-2010', 'Year 2010-2011'].
        sample_rows_per_sheet: Optional limit on rows per sheet for rapid prototyping/testing.

    Returns:
        Concatenated DataFrame of raw transaction rows.
    """
    root = get_project_root()
    path = Path(file_path) if file_path is not None else (root / "data" / "raw" / "uci_online_retail_ii" / "online_retail_II.xlsx")

    if not path.is_absolute():
        path = (root / path).resolve()

    if not path.is_file():
        raise FileNotFoundError(f"Raw dataset file not found: {path}")

    sheets_to_load = sheets or ["Year 2009-2010", "Year 2010-2011"]
    dfs = []

    logger.info(f"Loading UCI raw workbook from: {path.name}")
    for sheet in sheets_to_load:
        logger.info(f"Loading sheet '{sheet}' (sample limit: {sample_rows_per_sheet})...")
        df_sheet = pd.read_excel(path, sheet_name=sheet, nrows=sample_rows_per_sheet)
        df_sheet["_sheet_source"] = sheet
        dfs.append(df_sheet)

    combined_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Loaded total {len(combined_df):,} raw transaction rows from {len(sheets_to_load)} sheets.")
    return combined_df
