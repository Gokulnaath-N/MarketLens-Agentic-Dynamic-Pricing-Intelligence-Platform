"""Deterministic chronological train / validation / test dataset splitting."""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple
import pandas as pd

from marketlens.logging_config import get_logger

logger = get_logger("marketlens.data.split")


class SplitValidationError(Exception):
    """Raised when temporal split parameters or cutoffs violate chronological integrity."""

    pass


def chronological_split(
    df: pd.DataFrame,
    time_col: str = "period_start",
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    train_end: Optional[pd.Timestamp | str] = None,
    val_end: Optional[pd.Timestamp | str] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """Chronologically split a time series DataFrame into train, validation, and test subsets.

    Args:
        df: DataFrame containing a datetime column `time_col`.
        time_col: Column name containing timestamps or period starts.
        train_ratio: Proportion of unique time periods for training (if explicit dates not given).
        val_ratio: Proportion of unique time periods for validation.
        test_ratio: Proportion of unique time periods for testing.
        train_end: Optional explicit timestamp marking the end of the training window (inclusive).
        val_end: Optional explicit timestamp marking the end of the validation window (inclusive).

    Returns:
        Tuple of (train_df, val_df, test_df, split_metadata_dict).

    Raises:
        SplitValidationError: On overlapping windows or invalid ratios.
    """
    if df.empty:
        raise SplitValidationError("Cannot split empty DataFrame.")

    if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
        raise SplitValidationError(f"Column '{time_col}' must be datetime.")

    unique_dates = df[time_col].drop_duplicates().sort_values().reset_index(drop=True)
    n_periods = len(unique_dates)

    if n_periods < 5:
        raise SplitValidationError(f"Too few distinct time periods ({n_periods}) for chronological splitting.")

    # Determine cutoff dates
    if train_end is not None and val_end is not None:
        t_end = pd.to_datetime(train_end)
        v_end = pd.to_datetime(val_end)
        if not (unique_dates.min() <= t_end < v_end <= unique_dates.max()):
            raise SplitValidationError(
                f"Invalid explicit cutoffs: train_end ({t_end}) must precede val_end ({v_end})."
            )
    else:
        # Ratio-based division on sorted chronological periods
        total_ratio = train_ratio + val_ratio + test_ratio
        if abs(total_ratio - 1.0) > 1e-4:
            raise SplitValidationError(f"Split ratios must sum to 1.0, got {total_ratio:.3f}")

        train_cutoff_idx = int(n_periods * train_ratio)
        val_cutoff_idx = int(n_periods * (train_ratio + val_ratio))

        # Ensure at least 1 period in each split
        train_cutoff_idx = max(1, min(train_cutoff_idx, n_periods - 2))
        val_cutoff_idx = max(train_cutoff_idx + 1, min(val_cutoff_idx, n_periods - 1))

        t_end = unique_dates.iloc[train_cutoff_idx - 1]
        v_end = unique_dates.iloc[val_cutoff_idx - 1]

    # Partition data
    train_df = df[df[time_col] <= t_end].copy()
    val_df = df[(df[time_col] > t_end) & (df[time_col] <= v_end)].copy()
    test_df = df[df[time_col] > v_end].copy()

    # Integrity verification: strict non-overlapping boundaries
    if not train_df.empty and not val_df.empty:
        assert train_df[time_col].max() < val_df[time_col].min(), "Leakage detected: train overlap with validation!"
    if not val_df.empty and not test_df.empty:
        assert val_df[time_col].max() < test_df[time_col].min(), "Leakage detected: validation overlap with test!"

    metadata: Dict[str, Any] = {
        "time_column": time_col,
        "total_periods": n_periods,
        "train": {
            "start": str(train_df[time_col].min()) if not train_df.empty else None,
            "end": str(train_df[time_col].max()) if not train_df.empty else None,
            "row_count": len(train_df),
            "period_count": train_df[time_col].nunique(),
        },
        "validation": {
            "start": str(val_df[time_col].min()) if not val_df.empty else None,
            "end": str(val_df[time_col].max()) if not val_df.empty else None,
            "row_count": len(val_df),
            "period_count": val_df[time_col].nunique(),
        },
        "test": {
            "start": str(test_df[time_col].min()) if not test_df.empty else None,
            "end": str(test_df[time_col].max()) if not test_df.empty else None,
            "row_count": len(test_df),
            "period_count": test_df[time_col].nunique(),
        },
    }

    logger.info(
        f"Chronological split completed: Train [{metadata['train']['start']} -> {metadata['train']['end']}] ({metadata['train']['row_count']} rows), "
        f"Val [{metadata['validation']['start']} -> {metadata['validation']['end']}] ({metadata['validation']['row_count']} rows), "
        f"Test [{metadata['test']['start']} -> {metadata['test']['end']}] ({metadata['test']['row_count']} rows)."
    )
    return train_df, val_df, test_df, metadata
