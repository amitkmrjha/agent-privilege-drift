"""Unit tests for the LLM layer. No network: a fake completion function stands in for LiteLLM."""

from pathlib import Path
from typing import Any

import litellm
import pytest

from privilege_drift.llm import (
    LLMClient,
    MissingCredentialError,
    ResponseCache,
    load_models_config,
)
from privilege_drift.llm.config import ModelsConfig

MODELS_YAML = Path(__file__).parents[1] / "configs" / "models.yaml"
MESSAGES = [{"role": "user", "content": "Reply with exactly: ready"}]


class FakeCompletion:
    """Records calls and returns a canned LiteLLM response."""

    def __init__(self, text: str = "ready", prompt_tokens: int = 12) -> None:
        self.calls: list[dict[str, Any]] = []
        self.text = text
        self.prompt_tokens = prompt_tokens

    def __call__(self, **kwargs: Any) -> litellm.ModelResponse:
        self.calls.append(kwargs)
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


@pytest.fixture
def config() -> ModelsConfig:
    return load_models_config(MODELS_YAML)


def test_config_has_shared_sampling_and_both_models(config: ModelsConfig) -> None:
    assert config.sampling.temperature == 0.2
    assert config.sampling.top_p == 0.9
    assert config.sampling.max_tokens == 2048
    assert config.spec("llama").litellm_model.startswith("ollama/llama3.1:8b-instruct")
    assert config.spec("llama").num_ctx == 8192
    assert config.spec("frontier").api_key_env == "GEMINI_API_KEY"


def test_unknown_model_key_is_a_clear_error(config: ModelsConfig) -> None:
    with pytest.raises(KeyError, match="unknown model key"):
        config.spec("nope")


def test_switching_frontier_model_is_a_one_line_change(tmp_path: Path) -> None:
    text = MODELS_YAML.read_text()
    swapped = text.replace("gemini/gemini-2.5-flash", "anthropic/claude-sonnet-4-5")
    assert swapped.count("\n") == text.count("\n")  # same number of lines
    changed = [a for a, b in zip(text.splitlines(), swapped.splitlines(), strict=True) if a != b]
    assert len(changed) == 1
    path = tmp_path / "models.yaml"
    path.write_text(swapped)
    assert load_models_config(path).spec("frontier").litellm_model == "anthropic/claude-sonnet-4-5"


def test_call_passes_shared_sampling_seed_and_num_ctx(config: ModelsConfig) -> None:
    fake = FakeCompletion()
    result = LLMClient(config, completion_fn=fake).complete(MESSAGES, model_key="llama", seed=7)
    call = fake.calls[0]
    assert call["model"] == "ollama/llama3.1:8b-instruct-q4_K_M"
    assert (call["temperature"], call["top_p"], call["max_tokens"]) == (0.2, 0.9, 2048)
    assert call["seed"] == 7
    assert call["num_ctx"] == 8192
    assert call["api_base"] == "http://localhost:11434"
    assert result.text == "ready"
    assert (result.tokens_in, result.tokens_out) == (12, 3)
    assert result.finish_reason == "stop"
    assert result.latency_s >= 0
    assert result.raw["choices"][0]["message"]["content"] == "ready"
    assert result.cached is False


def test_ollama_base_url_comes_from_environment(
    config: ModelsConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OLLAMA_API_BASE", "http://host.docker.internal:11434")
    fake = FakeCompletion()
    LLMClient(config, completion_fn=fake).complete(MESSAGES, model_key="llama", seed=1)
    assert fake.calls[0]["api_base"] == "http://host.docker.internal:11434"


def test_frontier_needs_its_api_key(config: ModelsConfig, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    fake = FakeCompletion()
    with pytest.raises(MissingCredentialError, match="GEMINI_API_KEY"):
        LLMClient(config, completion_fn=fake).complete(MESSAGES, model_key="frontier", seed=1)
    assert fake.calls == []
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    LLMClient(config, completion_fn=fake).complete(MESSAGES, model_key="frontier", seed=1)
    assert fake.calls[0]["api_key"] == "test-key"
    assert "num_ctx" not in fake.calls[0]


def test_cache_hit_skips_the_model_and_marks_result(config: ModelsConfig, tmp_path: Path) -> None:
    fake = FakeCompletion()
    client = LLMClient(config, cache=ResponseCache(tmp_path), completion_fn=fake)
    first = client.complete(MESSAGES, model_key="llama", seed=1)
    second = client.complete(MESSAGES, model_key="llama", seed=1)
    assert len(fake.calls) == 1
    assert (first.cached, second.cached) == (False, True)
    assert second.text == first.text


def test_cache_key_depends_on_seed_prompt_and_model(config: ModelsConfig, tmp_path: Path) -> None:
    fake = FakeCompletion()
    client = LLMClient(config, cache=ResponseCache(tmp_path), completion_fn=fake)
    client.complete(MESSAGES, model_key="llama", seed=1)
    client.complete(MESSAGES, model_key="llama", seed=2)
    client.complete([{"role": "user", "content": "other"}], model_key="llama", seed=1)
    assert len(fake.calls) == 3


def test_no_cache_by_default(config: ModelsConfig) -> None:
    fake = FakeCompletion()
    client = LLMClient(config, completion_fn=fake)
    client.complete(MESSAGES, model_key="llama", seed=1)
    client.complete(MESSAGES, model_key="llama", seed=1)
    assert len(fake.calls) == 2


def test_truncation_flag_when_reported_prompt_shrinks_below_estimate(config: ModelsConfig) -> None:
    long_prompt = [{"role": "user", "content": "word " * 1000}]
    # Ollama trimmed the prompt: it reports 130 tokens for a ~1,000-token prompt.
    flagged = LLMClient(config, completion_fn=FakeCompletion(prompt_tokens=130)).complete(
        long_prompt, model_key="llama", seed=1
    )
    assert flagged.possible_truncation is True
    ok = LLMClient(config, completion_fn=FakeCompletion(prompt_tokens=1020)).complete(
        long_prompt, model_key="llama", seed=1
    )
    assert ok.possible_truncation is False


def test_truncation_flag_when_prompt_fills_the_context(config: ModelsConfig) -> None:
    result = LLMClient(config, completion_fn=FakeCompletion(prompt_tokens=8192)).complete(
        MESSAGES, model_key="llama", seed=1
    )
    assert result.possible_truncation is True
