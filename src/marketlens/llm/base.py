"""Provider-neutral LLM service abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """Base exception for LLM provider errors."""
    pass


class LLMAuthenticationError(LLMError):
    """Raised when provider credentials are missing or invalid."""
    pass


class LLMTimeoutError(LLMError):
    """Raised when an external LLM request times out."""
    pass


class LLMSchemaValidationError(LLMError):
    """Raised when LLM output fails validation against the target Pydantic schema."""
    pass


class BaseLLMService(ABC):
    """Abstract interface for LLM services supporting structured extraction and text generation."""

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> T:
        """Generate a schema-validated structured object from an input prompt."""
        raise NotImplementedError

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate unstructured text completion."""
        raise NotImplementedError
