"""The stop sequence is sent to the provider and is part of the cache key."""

from collections.abc import Sequence
from pathlib import Path

from privilege_drift.llm import ChatMessage, ResponseCache, load_models_config
from test_llm import MESSAGES, FakeCompletion, make_client

CONFIG = load_models_config(Path(__file__).parents[1] / "configs" / "models.yaml")


def test_stop_sequences_reach_the_provider() -> None:
    fake = FakeCompletion()
    make_client(CONFIG, fake).complete(MESSAGES, model_key="llama", seed=1, stop=["Observation:"])
    assert fake.calls[0]["stop"] == ["Observation:"]


def test_no_stop_means_no_stop_parameter() -> None:
    fake = FakeCompletion()
    make_client(CONFIG, fake).complete(MESSAGES, model_key="llama", seed=1)
    assert "stop" not in fake.calls[0]


def test_the_cache_distinguishes_calls_that_differ_only_in_stop(tmp_path: Path) -> None:
    fake = FakeCompletion()
    client = make_client(CONFIG, fake, cache=ResponseCache(tmp_path))
    messages: Sequence[ChatMessage] = MESSAGES
    client.complete(messages, model_key="llama", seed=1)
    client.complete(messages, model_key="llama", seed=1, stop=["Observation:"])
    client.complete(messages, model_key="llama", seed=1, stop=["Observation:"])
    assert len(fake.calls) == 2  # the third call is a cache hit
