"""429 handling inside one model call: exponential back-off, then fixed, with jitter. No network."""

from collections.abc import Sequence
from typing import Any

import litellm
import pytest
from litellm.exceptions import RateLimitError

from privilege_drift.llm import (
    ChatMessage,
    LLMCallError,
    LLMClient,
    LLMRateLimitError,
    ModelsConfig,
    ModelSpec,
    QuotaExhaustedError,
    RateLimitRetry,
    load_models_config,
    retry_after_seconds,
)
from test_llm import MESSAGES, MODELS_YAML


def too_many(text: str = "You exceeded your current quota") -> RateLimitError:
    return RateLimitError(message=text, llm_provider="gemini", model="gemini/x")


class Scripted:
    """Raises the scripted errors in order, then answers."""

    def __init__(self, errors: list[Exception]) -> None:
        self.errors = list(errors)
        self.calls: list[dict[str, Any]] = []

    def __call__(self, **kwargs: Any) -> litellm.ModelResponse:
        self.calls.append(kwargs)
        if self.errors:
            raise self.errors.pop(0)
        return litellm.ModelResponse(
            model=kwargs["model"],
            choices=[
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": "ready"},
                }
            ],
            usage={"prompt_tokens": 12, "completion_tokens": 3, "total_tokens": 15},
        )


def client(
    errors: list[Exception],
    retry: RateLimitRetry,
    sleeps: list[float],
    rand: float = 0.5,
) -> tuple[LLMClient, Scripted]:
    config: ModelsConfig = load_models_config(MODELS_YAML).model_copy(
        update={"rate_limit_retry": retry}
    )
    fake = Scripted(errors)

    def count_tokens(model: str, messages: Sequence[ChatMessage]) -> int:
        return 12

    def fingerprint(spec: ModelSpec, api_base: str | None) -> str | None:
        return None

    made = LLMClient(
        config,
        completion_fn=fake,
        token_counter=count_tokens,
        environ={"GEMINI_API_KEY": "test-key"},
        fingerprint_fn=fingerprint,
        sleep=sleeps.append,
        rand=lambda: rand,
    )
    return made, fake


def go(made: LLMClient) -> Any:
    return made.complete(MESSAGES, model_key="frontier", seed=7)


# ---- the waits ------------------------------------------------------------------------------


def test_waits_double_up_to_the_cap_and_then_stay_fixed() -> None:
    retry = RateLimitRetry(attempts=8, first_wait_s=10, max_wait_s=40, jitter=0.0)
    waits = [retry.wait_s(n, hint_s=None, rand=0.5) for n in range(1, 8)]
    assert waits == [10, 20, 40, 40, 40, 40, 40]  # exponential, then a fixed wait at the cap


def test_jitter_staggers_the_waits_within_the_set_fraction() -> None:
    retry = RateLimitRetry(first_wait_s=100, max_wait_s=100, jitter=0.25)
    low = retry.wait_s(1, hint_s=None, rand=0.0)
    middle = retry.wait_s(1, hint_s=None, rand=0.5)
    high = retry.wait_s(1, hint_s=None, rand=0.999999)
    assert low == pytest.approx(75) and middle == pytest.approx(100)
    assert high == pytest.approx(125, abs=0.01)


def test_the_providers_own_wait_is_a_minimum() -> None:
    retry = RateLimitRetry(first_wait_s=10, max_wait_s=40, jitter=0.0)
    assert retry.wait_s(1, hint_s=70, rand=0.5) == 70  # longer than the back-off says
    assert retry.wait_s(3, hint_s=5, rand=0.5) == 40  # shorter: the back-off wins


def test_the_retry_settings_are_validated() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        RateLimitRetry(attempts=0)
    with pytest.raises(ValueError, match="jitter"):
        RateLimitRetry(jitter=1.0)
    with pytest.raises(ValueError, match="positive"):
        RateLimitRetry(first_wait_s=0)


def test_the_models_file_can_set_them_and_has_sensible_defaults() -> None:
    config = load_models_config(MODELS_YAML)
    assert config.rate_limit_retry.attempts >= 2 and config.rate_limit_retry.first_wait_s > 0
    assert config.rate_limit_retry.give_up_after_s > config.rate_limit_retry.max_wait_s


# ---- reading the provider's hint --------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "seconds"),
    [
        ('{"error": {"details": [{"retryDelay": "34s"}]}}', 34.0),
        ("Rate limit hit. Please retry in 7.5s.", 7.5),
        ("quota exceeded, retry after 30 seconds", 30.0),
        ("You exceeded your current quota", None),
    ],
)
def test_the_providers_wait_is_read_from_its_message(text: str, seconds: float | None) -> None:
    assert retry_after_seconds(too_many(text)) == seconds


# ---- the retries inside one call ---------------------------------------------------------------


def test_a_429_is_retried_in_place_and_the_call_then_succeeds() -> None:
    sleeps: list[float] = []
    retry = RateLimitRetry(attempts=5, first_wait_s=10, max_wait_s=40, jitter=0.0)
    made, fake = client([too_many(), too_many()], retry, sleeps)
    result = go(made)
    assert result.text == "ready" and len(fake.calls) == 3
    assert sleeps == [10, 20]
    assert result.latency_s < 1.0  # the waits are not counted as model time
    assert fake.calls[0] == fake.calls[1] == fake.calls[2]  # the identical request each time


def test_the_waits_follow_exponential_then_fixed_across_a_long_streak() -> None:
    sleeps: list[float] = []
    retry = RateLimitRetry(attempts=7, first_wait_s=10, max_wait_s=40, jitter=0.0)
    made, fake = client([too_many() for _ in range(6)], retry, sleeps)
    assert go(made).text == "ready"
    assert sleeps == [10, 20, 40, 40, 40, 40]


def test_when_the_tries_run_out_a_rate_limit_error_is_raised() -> None:
    sleeps: list[float] = []
    retry = RateLimitRetry(attempts=3, first_wait_s=10, max_wait_s=40, jitter=0.0)
    made, fake = client([too_many("quota A")] * 5, retry, sleeps)
    with pytest.raises(LLMRateLimitError, match="quota A") as info:
        go(made)
    assert isinstance(info.value, LLMCallError)  # still an ordinary call error to callers
    assert len(fake.calls) == 3 and sleeps == [10, 20]  # no wait after the last try


def test_a_very_long_wait_means_the_quota_is_exhausted_and_nothing_more_is_tried() -> None:
    sleeps: list[float] = []
    retry = RateLimitRetry(attempts=8, first_wait_s=10, max_wait_s=40, give_up_after_s=900)
    made, fake = client([too_many("Please retry in 5000s")], retry, sleeps)
    with pytest.raises(QuotaExhaustedError) as info:
        go(made)
    assert info.value.retry_after_s == 5000 and not isinstance(info.value, LLMCallError)
    assert len(fake.calls) == 1 and sleeps == []


def test_other_errors_are_not_retried_by_the_client() -> None:
    sleeps: list[float] = []
    made, fake = client([ConnectionError("refused")], RateLimitRetry(), sleeps)
    with pytest.raises(LLMCallError, match="ConnectionError") as info:
        go(made)
    assert not isinstance(info.value, LLMRateLimitError)
    assert len(fake.calls) == 1 and sleeps == []
