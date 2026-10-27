"""Unit tests for dataset registry, candidate scoring, and license hard-gates."""

from __future__ import annotations

import pytest
from marketlens.datasets.licenses import evaluate_hard_gates
from marketlens.datasets.models import CandidateDataset, LicenseInfo
from marketlens.datasets.registry import DatasetRegistry, compute_suitability_score


@pytest.fixture
def sample_candidate() -> CandidateDataset:
    lic = LicenseInfo(
        license_name="Creative Commons Attribution 4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        license_type="Open / Attribution",
        commercial_allowed=True,
        academic_allowed=True,
        requires_attribution=True,
        verification_date="2026-10-27",
    )
    return CandidateDataset(
        dataset_id="test_dataset",
        name="Test Dataset",
        role="test_role",
        publisher="Test Institution",
        citation="Test Author (2026). Test Dataset.",
        official_url="https://example.org/dataset",
        download_url="https://example.org/download.zip",
        license=lic,
        requires_auth=False,
        estimated_size_mb=25.0,
        has_sales_quantity=True,
        has_observed_price=True,
        has_timestamps=True,
    )


class TestDatasetRegistry:
    """Tests registry candidate lookup, registration, and scoring."""

    def test_default_candidates_registered(self):
        registry = DatasetRegistry()
        candidates = registry.list_candidates()
        assert len(candidates) >= 3

        ids = [c.dataset_id for c in candidates]
        assert "uci_online_retail_ii" in ids
        assert "olist_brazilian_ecommerce" in ids
        assert "m5_forecasting" in ids

    def test_get_candidate_by_id(self):
        registry = DatasetRegistry()
        uci = registry.get_candidate("uci_online_retail_ii")
        assert uci is not None
        assert uci.name == "UCI Online Retail II"
        assert uci.hard_gate_status == "passed"
        assert uci.decision == "selected"

    def test_get_nonexistent_candidate_returns_none(self):
        registry = DatasetRegistry()
        assert registry.get_candidate("non_existent_id") is None

    def test_register_duplicate_candidate_raises_valueerror(self, sample_candidate):
        registry = DatasetRegistry()
        registry.register_candidate(sample_candidate)
        with pytest.raises(ValueError, match="already registered"):
            registry.register_candidate(sample_candidate)

    def test_suitability_score_calculation(self, sample_candidate):
        score, dim_scores = compute_suitability_score(sample_candidate)
        assert 0.0 <= score <= 100.0
        assert "credibility" in dim_scores
        assert "forecasting_readiness" in dim_scores
        assert dim_scores["forecasting_readiness"] == 30.0 # qty, price, time all present


class TestLicenseHardGates:
    """Tests hard gate compliance and blocking behavior."""

    def test_open_license_with_no_auth_passes(self, sample_candidate):
        passed, reason = evaluate_hard_gates(sample_candidate, has_credentials=False)
        assert passed is True
        assert "passed" in reason.lower()

    def test_missing_license_name_fails(self, sample_candidate):
        sample_candidate.license.license_name = ""
        passed, reason = evaluate_hard_gates(sample_candidate, has_credentials=False)
        assert passed is False
        assert "missing or unknown" in reason

    def test_non_academic_license_fails(self, sample_candidate):
        sample_candidate.license.academic_allowed = False
        passed, reason = evaluate_hard_gates(sample_candidate, has_credentials=False)
        assert passed is False
        assert "does not permit research" in reason

    def test_credential_requirement_without_credentials_fails(self, sample_candidate):
        sample_candidate.requires_auth = True
        sample_candidate.auth_type = "API Key"
        passed, reason = evaluate_hard_gates(sample_candidate, has_credentials=False)
        assert passed is False
        assert "requires API Key" in reason

    def test_insecure_url_fails_hard_gate(self, sample_candidate):
        sample_candidate.official_url = "http://insecure.org/data"
        passed, reason = evaluate_hard_gates(sample_candidate, has_credentials=True)
        assert passed is False
        assert "insecure" in reason
