"""Detect silent prompt truncation.

Ollama drops tokens when a prompt exceeds `num_ctx`, and the prompt size it then reports is
SMALLER than what was sent (observed: a ~1,000-token prompt with num_ctx 256 reported 130). A
check that only looks for "reported size reached the limit" therefore misses it. A result is
suspect when either:

- the reported prompt size is at or near `num_ctx`, or
- the reported size is well below an independent pre-send estimate.

A flag means "review or exclude the run"; it does not mean the call failed.
"""

from __future__ import annotations

NEAR_LIMIT_FRACTION = 0.98
SHRUNK_FRACTION = 0.8


def detect_truncation(*, tokens_in: int, estimate: int, num_ctx: int) -> bool:
    """True when the prompt was probably truncated to fit `num_ctx`."""
    near_limit = tokens_in >= NEAR_LIMIT_FRACTION * num_ctx
    shrunk = tokens_in < SHRUNK_FRACTION * estimate
    return near_limit or shrunk
