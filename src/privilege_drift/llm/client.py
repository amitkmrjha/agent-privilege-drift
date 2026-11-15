"""One call interface for every model (open or frontier) through LiteLLM."""

from __future__ import annotations

import os
import time
from collections.abc import Callable, Sequence
from typing import Any

import litellm
from pydantic import BaseModel

from privilege_drift.llm.cache import ResponseCache, cache_key
from privilege_drift.llm.config import ModelsConfig, ModelSpec

DEFAULT_OLLAMA_BASE = "http://localhost:11434"
# Ollama silently drops tokens when a prompt exceeds num_ctx, and the prompt size it then reports
# is SMALLER than what was sent (observed: ~1,000-token prompt, num_ctx 256 -> 130 reported).
# So a result is flagged `possible_truncation` when either:
#   - the reported prompt size is at/near num_ctx, or
#   - the reported size is well below an independent pre-send estimate.
# A flag means "review or exclude"; it does not mean the call failed.
NEAR_LIMIT_FRACTION = 0.98
SHRUNK_FRACTION = 0.8

Message = dict[str, Any]
CompletionFn = Callable[..., Any]


class MissingCredentialError(RuntimeError):
    """The environment variable that should hold an API key is empty."""


class LLMResult(BaseModel):
    """Structured outcome of one model call."""

    text: str
    tokens_in: int
    tokens_out: int
    latency_s: float
    model_key: str
    model: str
    seed: int | None
    finish_reason: str | None
    tokens_in_estimate: int | None = None
    possible_truncation: bool = False
    cached: bool = False
    raw: dict[str, Any]


class LLMClient:
    """Calls models by key, applying shared sampling settings and an optional cache."""

    def __init__(
        self,
        config: ModelsConfig,
        *,
        cache: ResponseCache | None = None,
        completion_fn: CompletionFn | None = None,
    ) -> None:
        self.config = config
        self.cache = cache
        self._completion = completion_fn or litellm.completion

    def _request(self, spec: ModelSpec, seed: int | None) -> dict[str, Any]:
        """Parameters that define the request (and therefore the cache key)."""
        sampling = self.config.sampling
        params: dict[str, Any] = {
            "temperature": sampling.temperature,
            "top_p": sampling.top_p,
            "max_tokens": sampling.max_tokens,
        }
        if seed is not None:
            params["seed"] = seed
        if spec.num_ctx is not None:
            params["num_ctx"] = spec.num_ctx
        return params

    def _connection(self, spec: ModelSpec) -> dict[str, Any]:
        """Where and how to connect. Not part of the cache key."""
        conn: dict[str, Any] = {}
        if spec.litellm_model.startswith("ollama/"):
            base = spec.api_base or (spec.api_base_env and os.environ.get(spec.api_base_env))
            conn["api_base"] = base or DEFAULT_OLLAMA_BASE
        elif spec.api_base:
            conn["api_base"] = spec.api_base
        if spec.api_key_env:
            key = os.environ.get(spec.api_key_env)
            if not key:
                raise MissingCredentialError(f"{spec.api_key_env} is not set (see .env.example)")
            conn["api_key"] = key
        return conn

    def complete(
        self,
        messages: Sequence[Message],
        *,
        model_key: str,
        seed: int | None = None,
    ) -> LLMResult:
        spec = self.config.spec(model_key)
        params = self._request(spec, seed)
        key = cache_key({"model": spec.litellm_model, "messages": list(messages), "params": params})

        if self.cache is not None:
            hit = self.cache.get(key)
            if hit is not None:
                return LLMResult.model_validate({**hit, "cached": True})

        conn = self._connection(spec)
        start = time.perf_counter()
        response = self._completion(
            model=spec.litellm_model, messages=list(messages), **params, **conn
        )
        latency = time.perf_counter() - start

        choice = response.choices[0]
        usage = response.usage
        tokens_in = int(usage.prompt_tokens or 0)
        tokens_out = int(usage.completion_tokens or 0)
        estimate: int | None = None
        truncated = False
        if spec.num_ctx:
            estimate = int(litellm.token_counter(model=spec.litellm_model, messages=list(messages)))
            truncated = (
                tokens_in >= NEAR_LIMIT_FRACTION * spec.num_ctx
                or tokens_in < SHRUNK_FRACTION * estimate
            )

        result = LLMResult(
            text=choice.message.content or "",
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_s=latency,
            model_key=model_key,
            model=spec.litellm_model,
            seed=seed,
            finish_reason=choice.finish_reason,
            tokens_in_estimate=estimate,
            possible_truncation=truncated,
            raw=response.model_dump(),
        )
        if self.cache is not None:
            self.cache.put(key, result.model_dump(mode="json"))
        return result
