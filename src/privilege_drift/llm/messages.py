"""Chat message type shared by the LLM layer."""

from __future__ import annotations

from typing import Literal, TypedDict


class ChatMessage(TypedDict):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
