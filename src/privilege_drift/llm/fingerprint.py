"""Identify exactly which model weights answered a call.

A model tag such as `llama3.1:8b-instruct-q4_K_M` can be re-pointed at different weights, so the
tag alone is not an identity. For Ollama we read the content digest from the server. Other
providers expose no digest; for them pin the exact model version in `configs/models.yaml`.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import httpx

from privilege_drift.llm.config import ModelSpec

logger = logging.getLogger(__name__)

# (model spec, resolved api_base) -> digest, or None when there is nothing to report.
FingerprintFn = Callable[[ModelSpec, str | None], str | None]


class OllamaFingerprinter:
    """Looks up a model's digest from Ollama's `/api/tags`. Successful lookups are memoised."""

    def __init__(self, *, get: Callable[..., Any] = httpx.get, timeout_s: float = 5.0) -> None:
        self._get = get
        self._timeout_s = timeout_s
        self._memo: dict[tuple[str, str], str] = {}

    def __call__(self, spec: ModelSpec, api_base: str | None) -> str | None:
        if api_base is None or not spec.litellm_model.startswith("ollama/"):
            return None
        name = spec.litellm_model.removeprefix("ollama/")
        memo_key = (api_base, name)
        if memo_key in self._memo:
            return self._memo[memo_key]
        try:
            response = self._get(f"{api_base.rstrip('/')}/api/tags", timeout=self._timeout_s)
            response.raise_for_status()
            models = response.json().get("models", [])
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("could not read digest for %s from %s: %s", name, api_base, exc)
            return None
        digest = next((m.get("digest") for m in models if m.get("name") == name), None)
        if digest is None:
            logger.warning("model %s not found on %s", name, api_base)
            return None
        self._memo[memo_key] = str(digest)
        return str(digest)
