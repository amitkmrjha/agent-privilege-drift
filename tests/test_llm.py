"""LLMClient behaviour. No network: fakes stand in for LiteLLM, the environment and Ollama."""

import logging
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import litellm
import pytest
from litellm.exceptions import Timeout

from privilege_drift.llm import (
    ChatMessage,
    LLMCallError,
    LLMClient,
    LLMError,
    LLMTimeoutError,
    MissingCredentialError,
    ModelSpec,
    ResponseCache,
    load_models_config,
)
from privilege_drift.llm.config import ModelsConfig

MODELS_YAML = Path(__file__).parents[1] / "configs" / "models.yaml"
MESSAGES: list[ChatMessage] = [{"role": "user", "content": "Reply with exactly: ready"}]
DIGEST = "sha256:aaaa"


class FakeCompletion:
    """Records calls and returns a canned LiteLLM response (or raises)."""

    def __init__(
        self, text: str = "ready", prompt_tokens: int = 12, raises: Exception | None = None
    ) -> None:
        self.calls: list[dict[str, Any]] = []
        self.text = text
        self.prompt_tokens = prompt_tokens
        self.raises = raises

    def __call__(self, **kwargs: Any) -> litellm.ModelResponse:
        self.calls.append(kwargs)
        if self.raises is not None:
            raise self.raises
        return litellm.ModelResponse(
            model=kwargs["model"],
            choices=[
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": self.text},
                }
            ],
            usage={
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": 3,
                "total_tokens": self.prompt_tokens + 3,
            },
        )


def make_client(
    config: ModelsConfig,
    fake: FakeCompletion,
    *,
    cache: ResponseCache | None = None,
    environ: Mapping[str, str] | None = None,
    digest: str | None = DIGEST,
    estimate: int = 12,
) -> LLMClient:
    def fingerprint(spec: ModelSpec, api_base: str | None) -> str | None:
        return digest if spec.litellm_model.startswith("ollama/") else None

    def count_tokens(model: str, messages: Sequence[ChatMessage]) -> int:
        return estimate

    return LLMClient(
        config,
        cache=cache,
        completion_fn=fake,
        token_counter=count_tokens,
        environ={} if environ is None else environ,
        fingerprint_fn=fingerprint,
    )


@pytest.fixture
def config() -> ModelsConfig:
    return load_models_config(MODELS_YAML)


# ---- config --------------------------------------------------------------------------------


def test_config_has_shared_sampling_timeout_and_both_models(config: ModelsConfig) -> None:
    assert config.sampling.temperature == 0.2
    assert config.sampling.top_p == 0.9
    assert config.sampling.max_tokens == 2048
    assert config.request_timeout_s == 300
    assert config.spec("llama").litellm_model.startswith("ollama/llama3.1:8b-instruct")
    assert config.spec("llama").num_ctx == 8192
    assert config.spec("frontier").api_key_env == "GEMINI_API_KEY"


def test_unknown_model_key_is_a_clear_error(config: ModelsConfig) -> None:
    with pytest.raises(KeyError, match="unknown model key"):
        config.spec("nope")


def test_switching_frontier_model_is_a_one_line_change(tmp_path: Path) -> None:
    text = MODELS_YAML.read_text()
    swapped = text.replace("gemini/gemini-2.5-flash", "anthropic/claude-sonnet-4-5")
    changed = [a for a, b in zip(text.splitlines(), swapped.splitlines(), strict=True) if a != b]
    assert len(changed) == 1
    path = tmp_path / "models.yaml"
    path.write_text(swapped)
    assert load_models_config(path).spec("frontier").litellm_model == "anthropic/claude-sonnet-4-5"


# ---- the call ------------------------------------------------------------------------------


def test_call_passes_shared_sampling_seed_num_ctx_and_timeout(config: ModelsConfig) -> None:
    fake = FakeCompletion()
    result = make_client(config, fake).complete(MESSAGES, model_key="llama", seed=7)
    call = fake.calls[0]
    assert call["model"] == "ollama/llama3.1:8b-instruct-q4_K_M"
    assert (call["temperature"], call["top_p"], call["max_tokens"]) == (0.2, 0.9, 2048)
    assert (call["seed"], call["num_ctx"], call["timeout"]) == (7, 8192, 300)
    assert call["api_base"] == "http://localhost:11434"
    assert result.text == "ready"
    assert (result.tokens_in, result.tokens_out) == (12, 3)
    assert result.finish_reason == "stop"
    assert result.model_fingerprint == DIGEST
    assert result.latency_s >= 0
    assert result.raw["choices"][0]["message"]["content"] == "ready"
    assert result.cached is False


def test_ollama_base_url_comes_from_the_injected_environment(config: ModelsConfig) -> None:
    fake = FakeCompletion()
    env = {"OLLAMA_API_BASE": "http://host.docker.internal:11434"}
    make_client(config, fake, environ=env).complete(MESSAGES, model_key="llama", seed=1)
    assert fake.calls[0]["api_base"] == "http://host.docker.internal:11434"


def test_frontier_needs_its_api_key(config: ModelsConfig) -> None:
    fake = FakeCompletion()
    with pytest.raises(MissingCredentialError, match="GEMINI_API_KEY"):
        make_client(config, fake).complete(MESSAGES, model_key="frontier", seed=1)
    assert fake.calls == []
    client = make_client(config, fake, environ={"GEMINI_API_KEY": "test-key"})
    result = client.complete(MESSAGES, model_key="frontier", seed=1)
    assert fake.calls[0]["api_key"] == "test-key"
    assert "num_ctx" not in fake.calls[0]
    assert result.model_fingerprint is None


# ---- failures ------------------------------------------------------------------------------


def test_timeout_is_wrapped_and_chained(config: ModelsConfig) -> None:
    cause = Timeout("slow", "ollama/x", "ollama")
    fake = FakeCompletion(raises=cause)
    with pytest.raises(LLMTimeoutError, match="timed out after 300s") as info:
        make_client(config, fake).complete(MESSAGES, model_key="llama", seed=1)
    assert info.value.__cause__ is cause
    assert info.value.model_key == "llama"
    assert isinstance(info.value, LLMError)


def test_other_provider_errors_are_wrapped_in_one_type(config: ModelsConfig) -> None:
    cause = ConnectionError("refused")
    fake = FakeCompletion(raises=cause)
    with pytest.raises(LLMCallError, match="ConnectionError: refused") as info:
        make_client(config, fake).complete(MESSAGES, model_key="llama", seed=1)
    assert info.value.__cause__ is cause
    assert not isinstance(info.value, LLMTimeoutError)


# ---- cache rules ---------------------------------------------------------------------------


def test_cache_hit_skips_the_model_and_marks_result(config: ModelsConfig, tmp_path: Path) -> None:
    fake = FakeCompletion()
    client = make_client(config, fake, cache=ResponseCache(tmp_path))
    first = client.complete(MESSAGES, model_key="llama", seed=1)
    second = client.complete(MESSAGES, model_key="llama", seed=1)
    assert len(fake.calls) == 1
    assert (first.cached, second.cached) == (False, True)
    assert second.text == first.text


def test_cache_key_depends_on_seed_prompt_and_model(config: ModelsConfig, tmp_path: Path) -> None:
    fake = FakeCompletion()
    client = make_client(config, fake, cache=ResponseCache(tmp_path))
    client.complete(MESSAGES, model_key="llama", seed=1)
    client.complete(MESSAGES, model_key="llama", seed=2)
    client.complete([{"role": "user", "content": "other"}], model_key="llama", seed=1)
    assert len(fake.calls) == 3


def test_cache_key_depends_on_the_model_digest(config: ModelsConfig, tmp_path: Path) -> None:
    cache = ResponseCache(tmp_path)
    fake = FakeCompletion()
    make_client(config, fake, cache=cache, digest="sha256:old").complete(
        MESSAGES, model_key="llama", seed=1
    )
    fresh = make_client(config, fake, cache=cache, digest="sha256:new").complete(
        MESSAGES, model_key="llama", seed=1
    )
    assert len(fake.calls) == 2  # same tag, different weights: not served from cache
    assert fresh.model_fingerprint == "sha256:new"


def test_without_a_seed_nothing_is_cached(config: ModelsConfig, tmp_path: Path) -> None:
    fake = FakeCompletion()
    client = make_client(config, fake, cache=ResponseCache(tmp_path))
    client.complete(MESSAGES, model_key="llama")
    client.complete(MESSAGES, model_key="llama")
    assert len(fake.calls) == 2
    assert list(tmp_path.glob("*.json")) == []


def test_unknown_ollama_digest_disables_the_cache(
    config: ModelsConfig, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    fake = FakeCompletion()
    client = make_client(config, fake, cache=ResponseCache(tmp_path), digest=None)
    with caplog.at_level(logging.WARNING):
        client.complete(MESSAGES, model_key="llama", seed=1)
        client.complete(MESSAGES, model_key="llama", seed=1)
    assert len(fake.calls) == 2
    assert "model digest unavailable" in caplog.text


def test_invalid_cache_entry_is_a_miss(config: ModelsConfig, tmp_path: Path) -> None:
    cache = ResponseCache(tmp_path)
    fake = FakeCompletion()
    client = make_client(config, fake, cache=cache)
    client.complete(MESSAGES, model_key="llama", seed=1)
    (entry,) = tmp_path.glob("*.json")
    entry.write_text('{"text": "valid json but not an LLMResult"}')
    again = client.complete(MESSAGES, model_key="llama", seed=1)
    assert len(fake.calls) == 2
    assert again.cached is False


def test_no_cache_by_default(config: ModelsConfig) -> None:
    fake = FakeCompletion()
    client = make_client(config, fake)
    client.complete(MESSAGES, model_key="llama", seed=1)
    client.complete(MESSAGES, model_key="llama", seed=1)
    assert len(fake.calls) == 2


# ---- truncation and logging ----------------------------------------------------------------


def test_truncation_is_flagged_and_logged(
    config: ModelsConfig, caplog: pytest.LogCaptureFixture
) -> None:
    fake = FakeCompletion(prompt_tokens=130)  # Ollama trimmed the prompt
    with caplog.at_level(logging.WARNING):
        result = make_client(config, fake, estimate=1014).complete(
            MESSAGES, model_key="llama", seed=1
        )
    assert result.possible_truncation is True
    assert result.tokens_in_estimate == 1014
    assert "possible prompt truncation" in caplog.text


def test_normal_call_is_not_flagged(config: ModelsConfig) -> None:
    result = make_client(config, FakeCompletion(prompt_tokens=19), estimate=12).complete(
        MESSAGES, model_key="llama", seed=1
    )
    assert result.possible_truncation is False


def test_logs_never_contain_prompts_or_keys(
    config: ModelsConfig, caplog: pytest.LogCaptureFixture
) -> None:
    secret_prompt: list[ChatMessage] = [{"role": "user", "content": "SECRET-PROMPT-TEXT"}]
    client = make_client(config, FakeCompletion(), environ={"GEMINI_API_KEY": "SECRET-KEY"})
    with caplog.at_level(logging.DEBUG):
        client.complete(secret_prompt, model_key="frontier", seed=1)
        client.complete(secret_prompt, model_key="llama", seed=1)
    assert "SECRET-PROMPT-TEXT" not in caplog.text
    assert "SECRET-KEY" not in caplog.text
