"""Truncation detection, tested directly as a pure function."""

import pytest

from privilege_drift.llm.truncation import detect_truncation


@pytest.mark.parametrize(
    ("tokens_in", "estimate", "num_ctx", "expected"),
    [
        (19, 12, 8192, False),  # normal: template adds a few tokens
        (1291, 1289, 8192, False),  # the longest real ToolPrivBench prompt
        (130, 1014, 256, True),  # observed: Ollama trimmed ~1,000 tokens, reported 130
        (8192, 8000, 8192, True),  # filled the window
        (8029, 8000, 8192, True),  # just over 98% of the window
        (8028, 8000, 8192, False),  # just under 98% of the window
        (800, 1000, 8192, False),  # exactly 80% of the estimate is still fine
        (799, 1000, 8192, True),  # below 80% of the estimate
    ],
)
def test_detect_truncation(tokens_in: int, estimate: int, num_ctx: int, expected: bool) -> None:
    assert detect_truncation(tokens_in=tokens_in, estimate=estimate, num_ctx=num_ctx) is expected
