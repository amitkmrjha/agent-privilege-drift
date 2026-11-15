"""Exceptions raised by the LLM layer. Callers catch `LLMError` to handle any model failure."""

from __future__ import annotations


class LLMError(Exception):
    """Base class for every failure raised by the LLM layer."""


class MissingCredentialError(LLMError):
    """The environment variable that should hold an API key is empty."""


class LLMCallError(LLMError):
    """The model call failed. The original exception is chained as `__cause__`."""

    def __init__(self, message: str, *, model_key: str, model: str) -> None:
        super().__init__(message)
        self.model_key = model_key
        self.model = model


class LLMTimeoutError(LLMCallError):
    """The model did not answer within the configured timeout."""
