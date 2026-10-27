"""Dataset source adapters for specific publisher interfaces and extraction workflows."""

from marketlens.datasets.adapters.base import BaseDatasetAdapter
from marketlens.datasets.adapters.uci_online_retail_ii import UCIOnlineRetailIIAdapter

__all__ = ["BaseDatasetAdapter", "UCIOnlineRetailIIAdapter"]
