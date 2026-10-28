"""Deterministic offline mock LLM service for testing and demonstration."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel

from marketlens.llm.base import BaseLLMService, LLMSchemaValidationError
from marketlens.logging_config import get_logger

logger = get_logger("marketlens.llm.mock")

T = TypeVar("T", bound=BaseModel)


class MockLLMService(BaseLLMService):
    """Mock LLM adapter that produces deterministic structured responses without network calls."""

    def __init__(self, predefined_responses: Optional[Dict[str, Any]] = None):
        self.predefined_responses = predefined_responses or {}

    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> T:
        """Return a deterministic mock response adhering strictly to the requested schema."""
        logger.debug("Generating mock structured response...")

        # If a predefined response exists in the lookup table, use it
        for key, resp in self.predefined_responses.items():
            if key in prompt:
                if isinstance(resp, schema):
                    return resp
                if isinstance(resp, dict):
                    return schema.model_validate(resp)

        # Build schema-specific default mock data
        schema_fields = schema.model_fields
        mock_data: Dict[str, Any] = {}

        if "sentiment_label" in schema_fields:
            # Deterministic sentiment heuristic for mock testing
            lower_p = prompt.lower()
            if any(w in lower_p for w in ["terrible", "poor", "broken", "bad", "horrible", "defect"]):
                mock_data["sentiment_label"] = "negative"
                mock_data["sentiment_score"] = -0.8
                mock_data["aspects"] = ["product_quality"]
                mock_data["complaint_categories"] = ["perceived_low_quality"]
                mock_data["praise_categories"] = []
                mock_data["summary"] = "Customer reported product defect or poor quality."
                mock_data["evidence_excerpt"] = "product defect or poor quality"
            elif any(w in lower_p for w in ["great", "excellent", "love", "amazing", "good", "perfect"]):
                mock_data["sentiment_label"] = "positive"
                mock_data["sentiment_score"] = 0.8
                mock_data["aspects"] = ["product_quality"]
                mock_data["complaint_categories"] = []
                mock_data["praise_categories"] = ["high_satisfaction"]
                mock_data["summary"] = "Customer expressed high satisfaction with the item."
                mock_data["evidence_excerpt"] = "high satisfaction"
            else:
                mock_data["sentiment_label"] = "neutral"
                mock_data["sentiment_score"] = 0.0
                mock_data["aspects"] = []
                mock_data["complaint_categories"] = []
                mock_data["praise_categories"] = []
                mock_data["summary"] = "Customer provided neutral feedback."
                mock_data["evidence_excerpt"] = None

            mock_data["extraction_method"] = "mock"
            mock_data["model_provider"] = "mock_provider"
            mock_data["model_name"] = "mock-model-v1"
            mock_data["validation_status"] = "validated"

        # Populate any missing required fields from metadata or schema defaults
        if metadata:
            for k, v in metadata.items():
                if k in schema_fields and k not in mock_data:
                    mock_data[k] = v

        try:
            return schema.model_validate(mock_data)
        except Exception as e:
            raise LLMSchemaValidationError(f"Mock output validation failed: {e}") from e

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Return a deterministic summary text."""
        return "Deterministic mock text completion: Analysis completed without external API dependency."
