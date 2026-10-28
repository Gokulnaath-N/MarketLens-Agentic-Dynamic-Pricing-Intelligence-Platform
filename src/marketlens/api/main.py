"""MarketLens AI FastAPI entry point and application factory."""

from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from marketlens.api.routes import (
    datasets,
    experiments,
    forecasts,
    health,
    market_intelligence,
    pricing,
)
from marketlens.logging_config import get_logger

logger = get_logger("marketlens.api")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="MarketLens AI API",
        description="Dynamic Pricing Intelligence & Demand Forecasting REST API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS for local frontend development
    cors_origins_env = os.getenv("CORS_ORIGINS", "")
    if cors_origins_env:
        origins = [orig.strip() for orig in cors_origins_env.split(",") if orig.strip()]
    else:
        origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routers
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(datasets.router, prefix="/api/v1")
    app.include_router(forecasts.router, prefix="/api/v1")
    app.include_router(market_intelligence.router, prefix="/api/v1")
    app.include_router(pricing.router, prefix="/api/v1")
    app.include_router(experiments.router, prefix="/api/v1")

    @app.get("/")
    def root():
        return {
            "app": "MarketLens AI API",
            "version": "0.1.0",
            "status": "online",
            "docs": "/docs",
        }

    return app


app = create_app()
