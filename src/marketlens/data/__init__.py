"""MarketLens AI Data Module.

Canonical data contracts, cleaning, canonicalization, aggregation, and chronological splitting.
"""

from marketlens.data.contracts import CanonicalSalesRecord, DemandSeriesRecord, ProductRecord

__all__ = ["CanonicalSalesRecord", "DemandSeriesRecord", "ProductRecord"]
