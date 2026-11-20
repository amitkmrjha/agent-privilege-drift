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


class LLMRateLimitError(LLMCallError):
    """The provider kept answering 429 (quota hit) until the retries inside one call ran out.

    ``retry_after_s`` is the wait the provider asked for in its last answer, if it gave one.
    """

    def __init__(
        self, message: str, *, model_key: str, model: str, retry_after_s: float | None = None
    ) -> None:
        super().__init__(message, model_key=model_key, model=model)
        self.retry_after_s = retry_after_s


class QuotaExhaustedError(LLMError):
    """The provider asked for a wait too long to be worth it (a daily quota, for example).

    Not an ``LLMCallError``, so nothing retries it: the batch stops and can be resumed later.
    """

    def __init__(self, message: str, *, retry_after_s: float | None = None) -> None:
        super().__init__(message)
        self.retry_after_s = retry_after_s
