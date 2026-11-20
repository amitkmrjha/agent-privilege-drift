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
