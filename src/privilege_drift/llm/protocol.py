"""The small interface that callers (the agent, the IBAC classifier) need from a model client."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from privilege_drift.llm.client import LLMResult
from privilege_drift.llm.messages import ChatMessage


class Completer(Protocol):
    """Anything that can answer a chat. ``LLMClient`` satisfies it; tests pass fakes."""

    def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        model_key: str,
        seed: int | None = None,
        stop: Sequence[str] | None = None,
    ) -> LLMResult: ...
