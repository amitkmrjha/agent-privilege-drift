"""One call interface for every model (open or frontier) through LiteLLM.

`LLMClient.complete` is a short pipeline: resolve the model, try the cache, call the model,
build a structured result, store it. Everything with side effects (the model call, the
environment, token counting, digest lookup, the cache) is passed in, so each piece can be
replaced in tests and nothing is read from global state inside the methods.
"""

from __future__ import annotations

import logging
import os
import random
import re
import time
from collections.abc import Callable, Mapping, Sequence
from typing import Any

import litellm
from litellm.exceptions import RateLimitError, Timeout
from pydantic import BaseModel, ValidationError

from privilege_drift.llm.cache import ResponseCache, cache_key
from privilege_drift.llm.config import ModelsConfig, ModelSpec
from privilege_drift.llm.errors import (
    LLMCallError,
    LLMRateLimitError,
    LLMTimeoutError,
    MissingCredentialError,
    QuotaExhaustedError,
)
from privilege_drift.llm.fingerprint import FingerprintFn, OllamaFingerprinter
from privilege_drift.llm.messages import ChatMessage
from privilege_drift.llm.truncation import detect_truncation

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_BASE = "http://localhost:11434"

CompletionFn = Callable[..., Any]
TokenCounter = Callable[[str, Sequence[ChatMessage]], int]


class LLMResult(BaseModel):
    """Structured outcome of one model call."""

    text: str
    tokens_in: int
    tokens_out: int
    latency_s: float
    model_key: str
    model: str
    model_fingerprint: str | None = None
    seed: int | None
    finish_reason: str | None
    tokens_in_estimate: int | None = None
    possible_truncation: bool = False
    cached: bool = False
    raw: dict[str, Any]


class _Parsed(BaseModel):
    """The few fields we read from a provider response."""

    text: str
    tokens_in: int
    tokens_out: int
    finish_reason: str | None
    raw: dict[str, Any]


def _parse_response(response: Any) -> _Parsed:
    """The only place that touches the untyped provider response."""
    choice = response.choices[0]
    usage = getattr(response, "usage", None)
    return _Parsed(
        text=choice.message.content or "",
        tokens_in=int(getattr(usage, "prompt_tokens", 0) or 0),
        tokens_out=int(getattr(usage, "completion_tokens", 0) or 0),
        finish_reason=choice.finish_reason,
        raw=response.model_dump(),
    )


def _litellm_token_count(model: str, messages: Sequence[ChatMessage]) -> int:
    return int(litellm.token_counter(model=model, messages=list(messages)))


# How providers phrase "wait this long": Gemini's JSON ("retryDelay": "34s"), "Please retry in
# 34.5s", "retry after 30 seconds".
_RETRY_HINTS = (
    re.compile(r"retry[_ ]?(?:delay|after)?[\"']?\s*[:=]?\s*[\"']?(\d+(?:\.\d+)?)\s*s", re.I),
    re.compile(r"retry in (\d+(?:\.\d+)?)\s*s", re.I),
)


def retry_after_seconds(exc: BaseException) -> float | None:
    """The wait a provider asked for in a 429 answer, or ``None`` if it gave none."""
    text = str(exc)
    for pattern in _RETRY_HINTS:
        found = pattern.search(text)
        if found:
            return float(found.group(1))
    return None


class LLMClient:
    """Calls models by key, applying shared sampling settings and an optional cache."""

    def __init__(
        self,
        config: ModelsConfig,
        *,
        cache: ResponseCache | None = None,
        completion_fn: CompletionFn | None = None,
        token_counter: TokenCounter | None = None,
        environ: Mapping[str, str] | None = None,
        fingerprint_fn: FingerprintFn | None = None,
        sleep: Callable[[float], None] = time.sleep,
        rand: Callable[[], float] = random.random,
    ) -> None:
        self.config = config
        self._sleep = sleep
        self._rand = rand
        self._cache = cache
        self._completion = completion_fn or litellm.completion
        self._count_tokens = token_counter or _litellm_token_count
        self._environ = os.environ if environ is None else environ
        self._fingerprint = fingerprint_fn or OllamaFingerprinter()

    # ---- public ---------------------------------------------------------------------------

    def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        model_key: str,
        seed: int | None = None,
        stop: Sequence[str] | None = None,
    ) -> LLMResult:
        spec = self.config.spec(model_key)
        api_base = self._api_base(spec)
        fingerprint = self._fingerprint(spec, api_base)
        params = self._sampling_params(spec, seed, stop)

        key = self._cache_key(spec, messages, params, fingerprint, seed)
        if key is not None:
            hit = self._cache_get(key)
            if hit is not None:
                return hit

        parsed, latency = self._call(spec, model_key, messages, params, api_base)
        result = self._build_result(spec, model_key, messages, parsed, latency, fingerprint, seed)

        if key is not None and self._cache is not None:
            self._cache.put(key, result.model_dump(mode="json"))
        logger.debug(
            "llm call model=%s seed=%s tokens_in=%d tokens_out=%d latency_s=%.2f",
            model_key,
            seed,
            result.tokens_in,
            result.tokens_out,
            result.latency_s,
        )
        return result

    # ---- request construction -------------------------------------------------------------

    def _sampling_params(
        self, spec: ModelSpec, seed: int | None, stop: Sequence[str] | None = None
    ) -> dict[str, Any]:
        """Parameters that define the request, and therefore the cache key."""
        sampling = self.config.sampling
        params: dict[str, Any] = {
            "temperature": sampling.temperature,
            "top_p": sampling.top_p,
            "max_tokens": sampling.max_tokens,
        }
        for name in spec.omit_params:
            params.pop(name, None)
        if seed is not None:
            params["seed"] = seed
        if stop:
            params["stop"] = list(stop)
        if spec.num_ctx is not None:
            params["num_ctx"] = spec.num_ctx
        return params

    def _api_base(self, spec: ModelSpec) -> str | None:
        if spec.litellm_model.startswith("ollama/"):
            from_env = self._environ.get(spec.api_base_env) if spec.api_base_env else None
            return spec.api_base or from_env or DEFAULT_OLLAMA_BASE
        return spec.api_base

    def _connection(self, spec: ModelSpec, api_base: str | None) -> dict[str, Any]:
        """How to connect. Never part of the cache key and never logged."""
        conn: dict[str, Any] = {"timeout": self.config.request_timeout_s}
        if api_base is not None:
            conn["api_base"] = api_base
        if spec.api_key_env:
            api_key = self._environ.get(spec.api_key_env)
            if not api_key:
                raise MissingCredentialError(f"{spec.api_key_env} is not set (see .env.example)")
            conn["api_key"] = api_key
        return conn

    # ---- cache ----------------------------------------------------------------------------

    def _cache_key(
        self,
        spec: ModelSpec,
        messages: Sequence[ChatMessage],
        params: dict[str, Any],
        fingerprint: str | None,
        seed: int | None,
    ) -> str | None:
        """A key, or None when this call must not be cached.

        Never cache without a seed (the output is meant to be random, and caching would freeze
        one draw). Never cache an Ollama model whose digest is unknown (the weights behind the
        tag could have changed).
        """
        if self._cache is None:
            return None
        if seed is None:
            logger.debug("not caching %s: no seed", spec.litellm_model)
            return None
        if spec.litellm_model.startswith("ollama/") and fingerprint is None:
            logger.warning("not caching %s: model digest unavailable", spec.litellm_model)
            return None
        return cache_key(
            {
                "model": spec.litellm_model,
                "fingerprint": fingerprint,
                "messages": list(messages),
                "params": params,
            }
        )

    def _cache_get(self, key: str) -> LLMResult | None:
        assert self._cache is not None
        stored = self._cache.get(key)
        if stored is None:
            return None
        try:
            return LLMResult.model_validate({**stored, "cached": True})
        except ValidationError as exc:
            logger.warning("ignoring invalid cache entry %s: %s", key[:12], exc.error_count())
            return None

    # ---- the model call -------------------------------------------------------------------

    def _call(
        self,
        spec: ModelSpec,
        model_key: str,
        messages: Sequence[ChatMessage],
        params: dict[str, Any],
        api_base: str | None,
    ) -> tuple[_Parsed, float]:
        conn = self._connection(spec, api_base)
        policy = self.config.rate_limit_retry
        for attempt in range(1, policy.attempts + 1):
            start = time.perf_counter()  # latency covers the call that worked, not the waiting
            try:
                response = self._completion(
                    model=spec.litellm_model, messages=list(messages), **params, **conn
                )
                return _parse_response(response), time.perf_counter() - start
            except Timeout as exc:
                raise LLMTimeoutError(
                    f"{model_key} timed out after {self.config.request_timeout_s:g}s",
                    model_key=model_key,
                    model=spec.litellm_model,
                ) from exc
            except RateLimitError as exc:
                hint = retry_after_seconds(exc)
                if hint is not None and hint > policy.give_up_after_s:
                    raise QuotaExhaustedError(
                        f"{model_key}: the provider asked for a wait of {hint:g}s, longer than "
                        f"the {policy.give_up_after_s:g}s limit, so the quota is treated as "
                        "exhausted; resume later",
                        retry_after_s=hint,
                    ) from exc
                if attempt == policy.attempts:
                    raise LLMRateLimitError(
                        f"{model_key} rate limited on all {policy.attempts} tries: "
                        f"{type(exc).__name__}: {str(exc)[:1000]}",
                        model_key=model_key,
                        model=spec.litellm_model,
                        retry_after_s=hint,
                    ) from exc
                wait = policy.wait_s(attempt, hint_s=hint, rand=self._rand())
                logger.warning(
                    "rate limited (429) model=%s try %d of %d, waiting %.1fs",
                    model_key,
                    attempt,
                    policy.attempts,
                    wait,
                )
                self._sleep(wait)
            except Exception as exc:  # adapter boundary: wrap whatever the provider raised
                raise LLMCallError(
                    f"{model_key} call failed: {type(exc).__name__}: {str(exc)[:300]}",
                    model_key=model_key,
                    model=spec.litellm_model,
                ) from exc
        raise AssertionError("unreachable: the loop returns or raises")  # pragma: no cover

    def _build_result(
        self,
        spec: ModelSpec,
        model_key: str,
        messages: Sequence[ChatMessage],
        parsed: _Parsed,
        latency: float,
        fingerprint: str | None,
        seed: int | None,
    ) -> LLMResult:
        estimate: int | None = None
        truncated = False
        if spec.num_ctx:
            estimate = self._count_tokens(spec.litellm_model, messages)
            truncated = detect_truncation(
                tokens_in=parsed.tokens_in, estimate=estimate, num_ctx=spec.num_ctx
            )
            if truncated:
                logger.warning(
                    "possible prompt truncation model=%s tokens_in=%d estimate=%d num_ctx=%d",
                    model_key,
                    parsed.tokens_in,
                    estimate,
                    spec.num_ctx,
                )
        return LLMResult(
            text=parsed.text,
            tokens_in=parsed.tokens_in,
            tokens_out=parsed.tokens_out,
            latency_s=latency,
            model_key=model_key,
            model=spec.litellm_model,
            model_fingerprint=fingerprint,
            seed=seed,
            finish_reason=parsed.finish_reason,
            tokens_in_estimate=estimate,
            possible_truncation=truncated,
            raw=parsed.raw,
        )
