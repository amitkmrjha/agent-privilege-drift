"""Digest lookup against a fake Ollama."""

import logging
from typing import Any

import httpx
import pytest

from privilege_drift.llm import ModelSpec, OllamaFingerprinter

OLLAMA = ModelSpec(litellm_model="ollama/llama3.1:8b-instruct-q4_K_M")
BASE = "http://localhost:11434"


class FakeResponse:
    def __init__(self, payload: Any) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Any:
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class FakeGet:
    def __init__(self, payload: Any = None, raises: Exception | None = None) -> None:
        self.payload = payload
        self.raises = raises
        self.urls: list[str] = []

    def __call__(self, url: str, **kwargs: Any) -> FakeResponse:
        self.urls.append(url)
        if self.raises is not None:
            raise self.raises
        return FakeResponse(self.payload)


TAGS = {"models": [{"name": "llama3.1:8b-instruct-q4_K_M", "digest": "sha256:46e0"}]}


def test_returns_digest_and_memoises() -> None:
    get = FakeGet(TAGS)
    fingerprint = OllamaFingerprinter(get=get)
    assert fingerprint(OLLAMA, BASE) == "sha256:46e0"
    assert fingerprint(OLLAMA, BASE) == "sha256:46e0"
    assert get.urls == [f"{BASE}/api/tags"]


def test_non_ollama_models_return_none_without_a_request() -> None:
    get = FakeGet(TAGS)
    spec = ModelSpec(litellm_model="gemini/gemini-2.5-flash")
    assert OllamaFingerprinter(get=get)(spec, None) is None
    assert get.urls == []


def test_model_not_pulled_returns_none(caplog: pytest.LogCaptureFixture) -> None:
    fingerprint = OllamaFingerprinter(get=FakeGet({"models": []}))
    with caplog.at_level(logging.WARNING):
        assert fingerprint(OLLAMA, BASE) is None
    assert "not found" in caplog.text


def test_server_down_returns_none_and_is_retried_next_time(
    caplog: pytest.LogCaptureFixture,
) -> None:
    down = FakeGet(raises=httpx.ConnectError("refused"))
    fingerprint = OllamaFingerprinter(get=down)
    with caplog.at_level(logging.WARNING):
        assert fingerprint(OLLAMA, BASE) is None
        assert fingerprint(OLLAMA, BASE) is None
    assert len(down.urls) == 2  # failures are not memoised
    assert "could not read digest" in caplog.text


def test_invalid_json_returns_none() -> None:
    assert OllamaFingerprinter(get=FakeGet(ValueError("bad json")))(OLLAMA, BASE) is None
