"""Abstract base adapter for dataset acquisition and unpacking."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from marketlens.datasets.models import AcquiredFile, CandidateDataset


class BaseDatasetAdapter(ABC):
    """Protocol for dataset adapters handling acquisition and safe unpacking."""

    @abstractmethod
    def acquire(self, candidate: CandidateDataset, dry_run: bool = False, force: bool = False) -> List[AcquiredFile]:
        """Acquire the dataset and return a list of verified raw files."""
        pass
