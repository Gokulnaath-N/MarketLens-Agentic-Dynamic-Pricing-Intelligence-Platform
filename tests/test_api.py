"""Tests for MarketLens AI FastAPI application endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from marketlens.api.main import app


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client fixture."""
    return TestClient(app)


def test_root_endpoint(client: TestClient) -> None:
    """Test root status endpoint."""
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "online"
    assert "version" in data


def test_health_endpoint(client: TestClient) -> None:
    """Test health endpoint."""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "timestamp_utc" in data


def test_system_status_endpoint(client: TestClient) -> None:
    """Test comprehensive system status endpoint."""
    resp = client.get("/api/v1/system/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["health"] == "operational"
    assert "modules" in data
    assert len(data["modules"]) >= 4
    module_names = [m["name"] for m in data["modules"]]
    assert "pricing_optimizer" in module_names
    assert "forecasting" in module_names


def test_datasets_endpoints(client: TestClient) -> None:
    """Test dataset list and profiling endpoints."""
    # List datasets
    resp = client.get("/api/v1/datasets")
    assert resp.status_code == 200
    datasets = resp.json()
    assert isinstance(datasets, list)
    assert len(datasets) > 0
    ds_ids = [d["dataset_id"] for d in datasets]
    assert "uci_online_retail_ii" in ds_ids

    # Profile existing dataset
    prof_resp = client.get("/api/v1/datasets/uci_online_retail_ii/profile")
    if prof_resp.status_code == 200:
        prof = prof_resp.json()
        assert prof["dataset_id"] == "uci_online_retail_ii"
        assert prof["row_count"] > 0
        assert "column_profiles" in prof

    # 404 on nonexistent dataset profile
    bad_resp = client.get("/api/v1/datasets/nonexistent_dataset_999/profile")
    assert bad_resp.status_code == 404


def test_forecasting_models_endpoint(client: TestClient) -> None:
    """Test forecast models list and evaluation retrieval."""
    resp = client.get("/api/v1/forecasts/models")
    assert resp.status_code == 200
    data = resp.json()
    assert "models" in data
    assert len(data["models"]) >= 2
    assert "NaivePersistence" in data["models"]
    assert data["target_column"] == "units_sold"


def test_live_forecast_endpoint(client: TestClient) -> None:
    """Test live on-demand forecast inference."""
    payload = {
        "product_id": "22423",
        "candidate_price": 10.0,
        "horizon_weeks": 2,
        "elasticity": -1.5,
        "base_demand": 50.0,
        "reference_price": 10.0,
    }
    resp = client.post("/api/v1/forecasts", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["product_id"] == "22423"
    assert data["predicted_demand"] == 50.0
    assert data["expected_revenue"] == 500.0


def test_market_intelligence_endpoints(client: TestClient) -> None:
    """Test customer reviews, sentiment, and competitor endpoints."""
    summary_resp = client.get("/api/v1/market-intelligence/summary")
    assert summary_resp.status_code == 200
    data = summary_resp.json()
    assert data["total_reviews_analyzed"] > 0
    assert "sentiment_breakdown" in data
    assert "competitors_monitored" in data

    rev_resp = client.get("/api/v1/market-intelligence/reviews")
    assert rev_resp.status_code == 200
    assert len(rev_resp.json()) > 0

    comp_resp = client.get("/api/v1/market-intelligence/competitors")
    assert comp_resp.status_code == 200
    assert len(comp_resp.json()) > 0


def test_pricing_optimization_revenue_endpoint(client: TestClient) -> None:
    """Test pricing optimization under revenue objective."""
    payload = {
        "product_id": "22423",
        "current_price": 10.0,
        "price_min": 8.0,
        "price_max": 14.0,
        "num_candidates": 7,
        "objective": "revenue",
        "currency": "GBP",
        "demand_context": {"base_demand": 50.0, "elasticity": -1.2},
    }
    resp = client.post("/api/v1/pricing/optimize", json=payload)
    assert resp.status_code == 200
    result = resp.json()
    assert result["status"] == "SUCCESS"
    assert result["recommended_price"] is not None
    assert result["expected_revenue"] > 0.0
    assert len(result["candidates"]) == 7


def test_pricing_optimization_profit_validation(client: TestClient) -> None:
    """Test profit optimization strictly rejects missing unit_cost."""
    payload = {
        "product_id": "22423",
        "current_price": 10.0,
        "price_min": 8.0,
        "price_max": 14.0,
        "objective": "profit",
        # unit_cost missing
    }
    resp = client.post("/api/v1/pricing/optimize", json=payload)
    assert resp.status_code == 422


def test_pricing_optimization_profit_success(client: TestClient) -> None:
    """Test profit optimization succeeds when positive unit_cost is provided."""
    payload = {
        "product_id": "22423",
        "current_price": 10.0,
        "price_min": 8.0,
        "price_max": 14.0,
        "num_candidates": 7,
        "objective": "profit",
        "unit_cost": 5.0,
        "min_gross_margin": 0.2,
        "currency": "GBP",
        "demand_context": {"base_demand": 50.0, "elasticity": -1.5},
    }
    resp = client.post("/api/v1/pricing/optimize", json=payload)
    assert resp.status_code == 200
    result = resp.json()
    assert result["status"] == "SUCCESS"
    assert result["recommended_price"] is not None
    assert result["estimated_profit"] is not None
    assert result["estimated_profit"] > 0.0


def test_experiments_endpoints(client: TestClient) -> None:
    """Test Phase 5 feature ablation study endpoints."""
    resp = client.get("/api/v1/experiments")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "ablation_type" in data[0]
        assert "delta_wape_vs_baseline" in data[0]

        detail_resp = client.get("/api/v1/experiments/phase5_feature_ablation")
        assert detail_resp.status_code in [200, 404]


def test_cors_headers(client: TestClient) -> None:
    """Test CORS headers on preflight requests."""
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
    }
    resp = client.options("/api/v1/pricing/optimize", headers=headers)
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"
