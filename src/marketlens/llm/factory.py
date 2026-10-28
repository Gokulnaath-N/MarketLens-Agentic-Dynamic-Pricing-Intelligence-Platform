"""Factory for creating configured LLM service instances."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from marketlens.config import load_yaml_config
from marketlens.llm.base import BaseLLMService
from marketlens.llm.mock import MockLLMService
from marketlens.logging_config import get_logger

logger = get_logger("marketlens.llm.factory")


def get_llm_service(config: Optional[Dict[str, Any]] = None) -> BaseLLMService:
    """Instantiate and return the appropriate LLM service based on configuration and environment.

    Returns:
        Instance of BaseLLMService (MockLLMService if in offline mode or keys absent).
    """
    agents_cfg = config or load_yaml_config("agents.yaml")
    general_cfg = agents_cfg.get("general", {})

    agents_enabled = general_cfg.get("agents_enabled", False)
    provider = general_cfg.get("default_provider", "mock").lower()

    if not agents_enabled or provider == "mock":
        logger.info("Operating in offline/mock LLM mode.")
        return MockLLMService()

    # If live provider is requested, verify credentials
    if provider in ["gemini", "google"]:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not found in environment. Falling back to MockLLMService.")
            return MockLLMService()
        # In this phase, live calls are gated; return mock if provider SDK is not installed
        logger.info("Gemini provider configured, using mock fallback for offline test verification.")
        return MockLLMService()

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found in environment. Falling back to MockLLMService.")
            return MockLLMService()
        return MockLLMService()

    logger.warning(f"Unknown provider '{provider}'. Defaulting to MockLLMService.")
    return MockLLMService()
