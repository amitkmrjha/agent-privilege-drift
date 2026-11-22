"""Live test against the local Ollama server. Opt in with: uv run pytest -m integration"""

import httpx
import pytest

from privilege_drift.llm import ChatMessage, LLMClient, load_models_config

pytestmark = pytest.mark.integration


def _ollama_up() -> bool:
    try:
        return httpx.get("http://localhost:11434/api/version", timeout=2).status_code == 200
    except httpx.HTTPError:
        return False


@pytest.mark.skipif(not _ollama_up(), reason="Ollama is not running")
def test_llama_returns_text_digest_and_same_seed_is_stable() -> None:
    client = LLMClient(load_models_config("configs/models.yaml"))
    msgs: list[ChatMessage] = [{"role": "user", "content": "Reply with exactly one word: ready"}]
    a = client.complete(msgs, model_key="llama", seed=1)
    b = client.complete(msgs, model_key="llama", seed=1)
    assert a.text.strip()
    assert a.model_fingerprint and a.model_fingerprint.startswith("46e0c10c039e")
    assert a.possible_truncation is False
    assert a.text == b.text
