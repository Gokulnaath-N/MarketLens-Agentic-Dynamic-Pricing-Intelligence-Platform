"""Dataset source registry and candidate evaluation engine.

Manages curated dataset candidate metadata, verifies authentication prerequisites,
computes objective suitability scores, and enforces hard-gate compliance decisions.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional
from marketlens.datasets.licenses import evaluate_hard_gates
from marketlens.datasets.models import CandidateDataset, LicenseInfo


def check_kaggle_credentials() -> bool:
    """Check if Kaggle credentials are configured locally via environment or file."""
    if os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY"):
        return True
    kaggle_json = os.path.expanduser("~/.kaggle/kaggle.json")
    return os.path.isfile(kaggle_json)


def compute_suitability_score(candidate: CandidateDataset) -> tuple[float, dict[str, float]]:
    """Compute transparent suitability score across 5 key dimensions (0.0 to 100.0).

    Dimensions:
    1. Source Credibility (20 pts): Reputable academic institution or peer-reviewed benchmark.
    2. License Clarity (20 pts): Standard open license (e.g. CC BY) with clear reuse terms.
    3. Forecasting Readiness (30 pts): Availability of timestamps, quantities, prices, and entity keys.
    4. Market Intelligence Signals (15 pts): Customer review text, competitor prices, or unit costs.
    5. Access Feasibility (15 pts): Direct public HTTPS download without login paywalls or excessive size.
    """
    scores: dict[str, float] = {}

    # 1. Source Credibility (20)
    scores["credibility"] = 20.0 if "archive.ics.uci.edu" in candidate.official_url or "kaggle.com" in candidate.official_url else 10.0

    # 2. License Clarity (20)
    if candidate.license.license_type.startswith("Open"):
        scores["license_clarity"] = 20.0
    elif candidate.license.academic_allowed:
        scores["license_clarity"] = 15.0
    else:
        scores["license_clarity"] = 0.0

    # 3. Forecasting Readiness (30)
    fc_score = 0.0
    if candidate.has_timestamps:
        fc_score += 10.0
    if candidate.has_sales_quantity:
        fc_score += 10.0
    if candidate.has_observed_price:
        fc_score += 10.0
    scores["forecasting_readiness"] = fc_score

    # 4. Market Intelligence Signals (15)
    mi_score = 0.0
    if candidate.has_customer_reviews:
        mi_score += 7.0
    if candidate.has_competitor_prices:
        mi_score += 5.0
    if candidate.has_unit_costs:
        mi_score += 3.0
    scores["market_signals"] = mi_score

    # 5. Access Feasibility (15)
    access_score = 0.0
    if not candidate.requires_auth:
        access_score += 10.0
    if candidate.estimated_size_mb and candidate.estimated_size_mb <= 250:
        access_score += 5.0
    elif candidate.estimated_size_mb and candidate.estimated_size_mb <= 500:
        access_score += 2.0
    scores["access_feasibility"] = access_score

    total = sum(scores.values())
    return round(total, 1), scores


class DatasetRegistry:
    """Registry of curated candidates and discovery manager for MarketLens AI."""

    def __init__(self):
        self._candidates: dict[str, CandidateDataset] = {}
        self._register_default_candidates()

    def _register_default_candidates(self) -> None:
        """Register the 4 core candidates investigated in the knowledge base."""
        has_kaggle = check_kaggle_credentials()

        # Candidate 1: UCI Online Retail II (Primary Sales Candidate)
        uci_lic = LicenseInfo(
            license_name="Creative Commons Attribution 4.0 International (CC BY 4.0)",
            license_url="https://creativecommons.org/licenses/by/4.0/",
            license_type="Open / Attribution",
            commercial_allowed=True,
            academic_allowed=True,
            requires_attribution=True,
            verification_date="2026-10-27",
        )
        uci = CandidateDataset(
            dataset_id="uci_online_retail_ii",
            name="UCI Online Retail II",
            role="primary_sales",
            publisher="UC Irvine Machine Learning Repository / Daqing Chen",
            citation="Chen, D. (2012). Online Retail II [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D",
            official_url="https://archive.ics.uci.edu/dataset/502/online+retail+ii",
            download_url="https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip",
            license=uci_lic,
            requires_auth=False,
            estimated_size_mb=45.0,
            has_sales_quantity=True,
            has_observed_price=True,
            has_timestamps=True,
            has_customer_reviews=False,
            has_competitor_prices=False,
            has_unit_costs=False,
            has_inventory_or_promotions=False,
            known_limitations=[
                "Does not contain competitor prices.",
                "Does not contain customer review text.",
                "Does not contain unit costs or product wholesale costs.",
                "Contains cancellation invoice codes ('C') and negative quantities requiring treatment in Phase 2.",
                "Historical transactions (2009-2011), not real-time conditions.",
            ],
        )
        self._evaluate_and_add(uci, has_credentials=True)

        # Candidate 2: Olist Brazilian E-Commerce Public Dataset
        olist_lic = LicenseInfo(
            license_name="Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)",
            license_url="https://creativecommons.org/licenses/by-nc-sa/4.0/",
            license_type="Non-Commercial Share-Alike",
            commercial_allowed=False,
            academic_allowed=True,
            requires_attribution=True,
            verification_date="2026-10-27",
        )
        olist = CandidateDataset(
            dataset_id="olist_brazilian_ecommerce",
            name="Brazilian E-Commerce Public Dataset by Olist",
            role="review_benchmark",
            publisher="Olist / Kaggle",
            citation="Olist. (2018). Brazilian E-Commerce Public Dataset by Olist [Dataset]. Kaggle. https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce",
            official_url="https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce",
            download_url="https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce",
            license=olist_lic,
            requires_auth=True,
            auth_type="Kaggle API Key (~/.kaggle/kaggle.json or KAGGLE_USERNAME/KAGGLE_KEY)",
            estimated_size_mb=120.0,
            has_sales_quantity=True,
            has_observed_price=True,
            has_timestamps=True,
            has_customer_reviews=True,
            has_competitor_prices=False,
            has_unit_costs=False,
            has_inventory_or_promotions=False,
            known_limitations=[
                "Requires Kaggle account credentials for API acquisition.",
                "CC BY-NC-SA license restricts commercial usage.",
                "Does not contain competitor prices or true unit wholesale costs.",
                "Product IDs are Brazilian market specific and cannot be merged with UCI.",
            ],
        )
        self._evaluate_and_add(olist, has_credentials=has_kaggle)

        # Candidate 3: M5 Forecasting Accuracy
        m5_lic = LicenseInfo(
            license_name="Kaggle Competition Rules / Makridakis Open Forecasting Center",
            license_url="https://www.kaggle.com/competitions/m5-forecasting-accuracy/rules",
            license_type="Competition Rules / Research",
            commercial_allowed=False,
            academic_allowed=True,
            requires_attribution=True,
            verification_date="2026-10-27",
        )
        m5 = CandidateDataset(
            dataset_id="m5_forecasting",
            name="M5 Forecasting Accuracy",
            role="forecasting_benchmark",
            publisher="University of Nicosia / Walmart / Kaggle",
            citation="Makridakis, S., et al. (2020). M5 Forecasting - Accuracy. Kaggle. https://www.kaggle.com/competitions/m5-forecasting-accuracy",
            official_url="https://www.kaggle.com/competitions/m5-forecasting-accuracy/data",
            download_url="https://www.kaggle.com/api/v1/competitions/data/download-all/m5-forecasting-accuracy",
            license=m5_lic,
            requires_auth=True,
            auth_type="Kaggle Competition Agreement & API Key",
            estimated_size_mb=550.0,
            has_sales_quantity=True,
            has_observed_price=True,
            has_timestamps=True,
            has_customer_reviews=False,
            has_competitor_prices=False,
            has_unit_costs=False,
            has_inventory_or_promotions=True,
            known_limitations=[
                "Requires Kaggle competition rules acceptance and API credentials.",
                "Size (>500MB) exceeds default Phase 1 download budget.",
                "No review text or competitor pricing.",
            ],
        )
        self._evaluate_and_add(m5, has_credentials=has_kaggle)

        # Candidate 4: Amazon Reviews 2023 (Category Subset)
        amazon_lic = LicenseInfo(
            license_name="Academic Research Use Only (UCSD McAuley Lab)",
            license_url="https://amazon-reviews-2023.github.io/",
            license_type="Academic Research",
            commercial_allowed=False,
            academic_allowed=True,
            requires_attribution=True,
            verification_date="2026-10-27",
        )
        amazon = CandidateDataset(
            dataset_id="amazon_reviews_2023",
            name="Amazon Reviews 2023 (Category Subset)",
            role="review_nlp_benchmark",
            publisher="McAuley Lab / UC San Diego",
            citation="Hou, Y., et al. (2024). Bridging Language and Items for Retrieval and Recommendation. arXiv:2403.03952",
            official_url="https://amazon-reviews-2023.github.io/",
            download_url=None, # Loaded via HuggingFace streaming if enabled
            license=amazon_lic,
            requires_auth=False,
            estimated_size_mb=2000.0,
            has_sales_quantity=False,
            has_observed_price=True,
            has_timestamps=True,
            has_customer_reviews=True,
            has_competitor_prices=False,
            has_unit_costs=False,
            has_inventory_or_promotions=False,
            known_limitations=[
                "Dataset is very large (>100GB full corpus); must only be streamed in small subsets.",
                "No daily transaction sales volumes or store identifiers.",
                "Product IDs do not join to UCI or Olist.",
            ],
        )
        self._evaluate_and_add(amazon, has_credentials=True)

    def _evaluate_and_add(self, candidate: CandidateDataset, has_credentials: bool) -> None:
        """Run hard-gate checks and scoring on candidate."""
        passed, reason = evaluate_hard_gates(candidate, has_credentials=has_credentials)
        score, dim_scores = compute_suitability_score(candidate)
        candidate.suitability_score = score
        candidate.dimension_scores = dim_scores

        if not passed:
            candidate.hard_gate_status = "blocked_credentials" if "Credentials" in reason else "blocked_license"
            candidate.hard_gate_reason = reason
            candidate.decision = "blocked"
            candidate.decision_reason = reason
        else:
            candidate.hard_gate_status = "passed"
            candidate.hard_gate_reason = reason
            if candidate.dataset_id == "uci_online_retail_ii":
                candidate.decision = "selected"
                candidate.decision_reason = "Primary sales dataset: Open CC BY 4.0 license, direct public download, meets all demand baseline requirements."
            else:
                candidate.decision = "optional"
                candidate.decision_reason = "Deferred as optional secondary benchmark."

        self._candidates[candidate.dataset_id] = candidate

    def get_candidate(self, dataset_id: str) -> Optional[CandidateDataset]:
        return self._candidates.get(dataset_id)

    def list_candidates(self) -> List[CandidateDataset]:
        return list(self._candidates.values())

    def register_candidate(self, candidate: CandidateDataset, has_credentials: bool = True) -> None:
        """Register a custom candidate."""
        if candidate.dataset_id in self._candidates:
            raise ValueError(f"Dataset ID '{candidate.dataset_id}' is already registered.")
        self._evaluate_and_add(candidate, has_credentials=has_credentials)
