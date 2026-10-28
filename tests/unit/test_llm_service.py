"""Unit tests for LLM abstraction layer: MockLLMService, RuleBasedReviewExtractor, and factory."""

import pytest
from pydantic import BaseModel, Field

from marketlens.agents.schemas import ExtractionMethod, ReviewInsightOutput, SentimentLabel
from marketlens.llm.base import BaseLLMService, LLMSchemaValidationError
from marketlens.llm.factory import get_llm_service
from marketlens.llm.mock import MockLLMService
from marketlens.llm.rule_based import RuleBasedReviewExtractor


class DummySchema(BaseModel):
    name: str = Field(..., min_length=2)
    score: int = Field(..., ge=0, le=100)


def test_mock_llm_service_review_insight():
    """Verify MockLLMService generates valid ReviewInsightOutput deterministically."""
    service = MockLLMService()
    prompt = 'Customer Review Data:\n"""This item is broken and terrible quality!"""'

    output = service.generate_structured(
        prompt=prompt,
        schema=ReviewInsightOutput,
        metadata={"review_id": "REV-MOCK-1", "product_id": "PROD-1"},
    )
    assert isinstance(output, ReviewInsightOutput)
    assert output.sentiment_label == SentimentLabel.NEGATIVE
    assert output.sentiment_score == -0.8
    assert output.extraction_method == ExtractionMethod.MOCK


def test_mock_llm_service_predefined_response():
    """Verify predefined response lookup in MockLLMService."""
    service = MockLLMService(predefined_responses={"special_key": {"name": "TargetItem", "score": 95}})
    res = service.generate_structured(
        prompt="Please analyze special_key payload",
        schema=DummySchema,
    )
    assert res.name == "TargetItem"
    assert res.score == 95


def test_rule_based_extractor_lexicon():
    """Verify RuleBasedReviewExtractor extracts sentiment and categories via lexicon matching."""
    extractor = RuleBasedReviewExtractor()

    # Positive test
    pos_res = extractor.extract("Fast shipping and great packaging, customer service was helpful!")
    assert pos_res["sentiment_label"] == "positive"
    assert pos_res["sentiment_score"] > 0
    assert "delivery_shipping" in pos_res["aspects"]
    assert "customer_service" in pos_res["aspects"]
    assert "packaging" in pos_res["aspects"]

    # Negative test
    neg_res = extractor.extract("Defective, expensive, overpriced and terrible product.")
    assert neg_res["sentiment_label"] == "negative"
    assert neg_res["sentiment_score"] < 0
    assert "product_quality" in neg_res["aspects"]
    assert "value_for_money" in neg_res["aspects"]


def test_llm_factory_offline_default():
    """Verify get_llm_service returns MockLLMService when in offline mode or keys absent."""
    cfg = {
        "general": {
            "agents_enabled": True,
            "default_provider": "mock",
        }
    }
    service = get_llm_service(cfg)
    assert isinstance(service, MockLLMService)
