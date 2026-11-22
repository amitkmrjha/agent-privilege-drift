"""Typed loader for ``configs/models.yaml``."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, field_validator

DEFAULT_MODELS_PATH = Path("configs/models.yaml")


class Sampling(BaseModel):
    """Decoding settings shared by every model so the arms are comparable."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    temperature: float
    top_p: float
    max_tokens: int


class RateLimitRetry(BaseModel):
    """How one model call is retried when the provider answers 429 (quota hit).

    The wait before retry number n is ``first_wait_s`` doubled n - 1 times, up to ``max_wait_s``
    and then fixed there (exponential, then fixed). Each wait is spread by +/- ``jitter`` so that
    retries are staggered rather than all landing on the same second. If the provider says how
    long to wait, the wait is at least that long; if it asks for more than ``give_up_after_s``
    the quota is treated as exhausted and nothing more is tried. The same request is sent each
    time (same messages, same seed), so a retried call is the call it replaces.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    attempts: int = 8  # tries per call, the first included
    first_wait_s: float = 15.0
    max_wait_s: float = 120.0
    jitter: float = 0.25
    give_up_after_s: float = 900.0

    @field_validator("attempts")
    @classmethod
    def _at_least_one_attempt(cls, value: int) -> int:
        if value < 1:
            raise ValueError("attempts must be at least 1")
        return value

    @field_validator("first_wait_s", "max_wait_s", "give_up_after_s")
    @classmethod
    def _positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("waits must be positive")
        return value

    @field_validator("jitter")
    @classmethod
    def _fraction(cls, value: float) -> float:
        if not 0.0 <= value < 1.0:
            raise ValueError("jitter must be at least 0 and below 1")
        return value

    def wait_s(self, retry_number: int, *, hint_s: float | None, rand: float) -> float:
        """Seconds to wait before retry ``retry_number`` (1 for the first retry).

        ``hint_s`` is the provider's own suggestion; ``rand`` is a number in [0, 1) that sets
        the jitter (0.5 means no change).
        """
        cap = max(self.max_wait_s, self.first_wait_s)
        base = min(self.first_wait_s * 2.0 ** (retry_number - 1), cap)
        if hint_s is not None:
            base = max(base, hint_s)
        return float(base * (1.0 + self.jitter * (2.0 * rand - 1.0)))


class ModelSpec(BaseModel):
    """How to reach one model through LiteLLM."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    litellm_model: str
    api_base: str | None = None
    api_base_env: str | None = None
    api_key_env: str | None = None
    num_ctx: int | None = None
    # Shared decoding settings this model's API rejects; they are left out of its requests.
    # Every use is a departure from "identical decoding for both arms" and must be reported.
    omit_params: tuple[str, ...] = ()

    @field_validator("omit_params")
    @classmethod
    def _only_omittable(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        bad = set(value) - {"temperature", "top_p"}
        if bad:
            raise ValueError(
                f"cannot omit {sorted(bad)}; only temperature and top_p can be left out"
            )
        return value


class ModelsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sampling: Sampling
    # Generous: the first call after a model is not loaded can take ~35 s on this machine.
    request_timeout_s: float = 300.0
    rate_limit_retry: RateLimitRetry = RateLimitRetry()
    models: dict[str, ModelSpec]

    def spec(self, model_key: str) -> ModelSpec:
        try:
            return self.models[model_key]
        except KeyError:
            known = ", ".join(sorted(self.models))
            raise KeyError(f"unknown model key {model_key!r}; known keys: {known}") from None


def load_models_config(path: Path | str = DEFAULT_MODELS_PATH) -> ModelsConfig:
    """Parse and validate the models file."""
    data = yaml.safe_load(Path(path).read_text())
    return ModelsConfig.model_validate(data)
