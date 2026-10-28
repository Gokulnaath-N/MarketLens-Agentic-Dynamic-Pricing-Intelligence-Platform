"""Deterministic rule-based lexicon and keyword extractor for review insights."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


POSITIVE_WORDS = {
    "great", "excellent", "good", "amazing", "love", "perfect", "wonderful", "fantastic",
    "best", "durable", "high quality", "satisfied", "recommend", "beautiful", "worth",
    "bargain", "fast", "superb", "brilliant", "delighted", "solid", "well-made"
}

NEGATIVE_WORDS = {
    "bad", "terrible", "poor", "broken", "awful", "horrible", "defect", "defective", "faulty",
    "useless", "waste", "cheap", "expensive", "disappointed", "damaged", "delayed",
    "slow", "never", "hate", "scam", "worst", "unacceptable", "flimsy", "return"
}

ASPECT_KEYWORDS = {
    "product_quality": ["quality", "material", "broken", "defect", "defective", "faulty", "durable", "craft", "flimsy", "solid", "finish"],
    "value_for_money": ["price", "expensive", "cheap", "worth", "bargain", "cost", "overpriced", "value"],
    "delivery_shipping": ["delivery", "shipping", "arrive", "delayed", "delay", "courier", "postage", "dispatch"],
    "customer_service": ["service", "refund", "support", "response", "seller", "agent", "contact"],
    "packaging": ["package", "packaging", "box", "wrap", "wrapped", "parcel"],
}


class RuleBasedReviewExtractor:
    """Extracts sentiment, aspects, and evidence from review text using deterministic rules."""

    def extract(self, text: str) -> Dict[str, Any]:
        """Perform lexicon-based sentiment and aspect extraction on sanitized review text.

        Args:
            text: Sanitized customer review text.

        Returns:
            Dict matching review insight output structure.
        """
        clean_text = text.strip()
        if not clean_text:
            return {
                "sentiment_label": "unknown",
                "sentiment_score": 0.0,
                "aspects": [],
                "complaint_categories": [],
                "praise_categories": [],
                "summary": "Empty review text.",
                "evidence_excerpt": None,
                "extraction_method": "rule_based",
                "model_provider": None,
                "model_name": None,
                "validation_status": "validated",
                "warnings": ["Review text was empty."],
            }

        lower_text = clean_text.lower()
        pos_matches = [w for w in POSITIVE_WORDS if re.search(r"\b" + re.escape(w) + r"\b", lower_text)]
        neg_matches = [w for w in NEGATIVE_WORDS if re.search(r"\b" + re.escape(w) + r"\b", lower_text)]

        pos_count = len(pos_matches)
        neg_count = len(neg_matches)
        total_sentiment_words = pos_count + neg_count

        # Score calculation in [-1.0, 1.0]
        if total_sentiment_words == 0:
            sentiment_score = 0.0
            sentiment_label = "neutral"
        else:
            sentiment_score = float((pos_count - neg_count) / total_sentiment_words)
            if sentiment_score > 0.15:
                sentiment_label = "positive"
            elif sentiment_score < -0.15:
                sentiment_label = "negative"
            elif pos_count > 0 and neg_count > 0:
                sentiment_label = "mixed"
            else:
                sentiment_label = "neutral"

        # Aspect extraction
        detected_aspects: List[str] = []
        for aspect, keywords in ASPECT_KEYWORDS.items():
            if any(re.search(r"\b" + re.escape(kw) + r"\b", lower_text) for kw in keywords):
                detected_aspects.append(aspect)

        # Categorize complaints vs praise
        complaint_categories: List[str] = []
        praise_categories: List[str] = []
        if sentiment_label in ["negative", "mixed"]:
            if "product_quality" in detected_aspects:
                complaint_categories.append("perceived_low_quality")
            if "value_for_money" in detected_aspects:
                complaint_categories.append("perceived_high_price")
            if "delivery_shipping" in detected_aspects:
                complaint_categories.append("delivery_delay_or_damage")
            if not complaint_categories:
                complaint_categories.append("general_dissatisfaction")

        if sentiment_label in ["positive", "mixed"]:
            if "product_quality" in detected_aspects:
                praise_categories.append("high_product_satisfaction")
            if "value_for_money" in detected_aspects:
                praise_categories.append("good_value_for_money")
            if not praise_categories:
                praise_categories.append("general_satisfaction")

        # Grounded evidence excerpt
        evidence_excerpt = None
        salient_words = neg_matches + pos_matches
        if salient_words:
            # Find the sentence containing the first salient word
            sentences = re.split(r"[.!?\n]+", clean_text)
            for s in sentences:
                s_strip = s.strip()
                if any(w in s_strip.lower() for w in salient_words):
                    evidence_excerpt = s_strip[:150]  # Cap length
                    break

        summary = (
            f"Customer expressed {sentiment_label} sentiment (score: {sentiment_score:.2f}) "
            f"mentioning {len(detected_aspects)} aspect(s)."
        )

        return {
            "sentiment_label": sentiment_label,
            "sentiment_score": round(sentiment_score, 2),
            "aspects": detected_aspects,
            "complaint_categories": complaint_categories,
            "praise_categories": praise_categories,
            "summary": summary,
            "evidence_excerpt": evidence_excerpt,
            "extraction_method": "rule_based",
            "model_provider": None,
            "model_name": None,
            "validation_status": "validated",
            "warnings": [],
        }
