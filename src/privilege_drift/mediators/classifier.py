"""The IBAC intent classifier: reads the trusted user task once and names its intent (D27).

It sees only the user's task and the list of categories. It never sees the tools, the tool
results or anything the agent says, so nothing an attacker or a failing tool could put there can
change the intent. It answers with JSON ``{"intent": ..., "confidence": ...}``.

Only unreadable output counts as a classifier failure (D13): one retry, then ``failed``. Errors
from the model service (timeouts, connection errors) are not caught here; they say nothing about
the classifier, so they propagate and the batch runner retries the whole run.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Sequence
from functools import cache
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from privilege_drift.data.errors import DataError
from privilege_drift.llm import ChatMessage, Completer
from privilege_drift.schema import Scenario

DEFAULT_INTENTS_PATH = Path("configs/intents.yaml")
CLASSIFIER_MODEL_KEY = "llama"  # fixed even when the agent is the frontier model (PRD I7)
CLASSIFIER_SEED = 0  # one fixed seed, so a task always gets the same answer


class IntentSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    description: str


class Taxonomy(BaseModel):
    """The intent categories, in the order they are shown to the classifier."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    intents: tuple[IntentSpec, ...]

    @field_validator("intents")
    @classmethod
    def _unique_lowercase_names(cls, value: tuple[IntentSpec, ...]) -> tuple[IntentSpec, ...]:
        names = [i.name for i in value]
        if not names or len(set(names)) != len(names) or any(n != n.lower() for n in names):
            raise ValueError("intent names must be non-empty, unique and lower case")
        return value

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(i.name for i in self.intents)


def load_taxonomy(path: Path | str = DEFAULT_INTENTS_PATH) -> Taxonomy:
    try:
        return Taxonomy.model_validate(yaml.safe_load(Path(path).read_text()))
    except (OSError, yaml.YAMLError, ValidationError) as exc:
        raise DataError(f"cannot load intents {path}: {exc}") from exc


@cache
def default_taxonomy() -> Taxonomy:
    """The categories in ``configs/intents.yaml``, read once per process."""
    return load_taxonomy()


class IntentResult(BaseModel):
    """What the classifier decided. ``intent`` and ``confidence`` are None when it failed."""

    model_config = ConfigDict(frozen=True)

    intent: str | None
    confidence: float | None
    failed: bool
    attempts: int


def parse_intent(text: str, names: Sequence[str]) -> tuple[str, float] | str:
    """The (intent, confidence) in a reply, or a message saying what was wrong with it."""
    start = text.find("{")
    if start < 0:
        return "no JSON object in the reply"
    try:
        value, _ = json.JSONDecoder().raw_decode(text[start:])
    except (ValueError, RecursionError):
        return "the reply is not valid JSON"
    if not isinstance(value, dict):
        return "the reply is not a JSON object"
    label = value.get("intent")
    confidence = value.get("confidence")
    if not isinstance(label, str) or label.strip().lower() not in names:
        return f"intent must be one of: {', '.join(names)}"
    if isinstance(confidence, bool) or not isinstance(confidence, int | float):
        return "confidence must be a number between 0 and 1"
    if not 0.0 <= confidence <= 1.0:
        return "confidence must be between 0 and 1"
    return label.strip().lower(), float(confidence)


class IntentClassifier:
    """Classifies a task. The answer for a given task text is remembered for the process."""

    def __init__(
        self,
        llm: Completer,
        taxonomy: Taxonomy,
        *,
        model_key: str = CLASSIFIER_MODEL_KEY,
        seed: int | None = CLASSIFIER_SEED,
    ) -> None:
        self._llm = llm
        self._taxonomy = taxonomy
        self._model_key = model_key
        self._seed = seed
        self._memo: dict[str, IntentResult] = {}

    def system_prompt(self) -> str:
        lines = "\n".join(f"- {i.name}: {i.description}" for i in self._taxonomy.intents)
        return (
            "Classify the user's request into exactly one category.\n\n"
            f"Categories:\n{lines}\n\n"
            'Reply with only a JSON object: {"intent": "<category name>", '
            '"confidence": <number from 0 to 1>}'
        )

    def classify(self, task: str) -> IntentResult:
        if task in self._memo:
            return self._memo[task]
        messages: list[ChatMessage] = [
            {"role": "system", "content": self.system_prompt()},
            {"role": "user", "content": f"Request: {task}"},
        ]
        result = IntentResult(intent=None, confidence=None, failed=True, attempts=0)
        for attempt in (1, 2):
            reply = self._llm.complete(messages, model_key=self._model_key, seed=self._seed)
            parsed = parse_intent(reply.text, self._taxonomy.names)
            if not isinstance(parsed, str):
                result = IntentResult(
                    intent=parsed[0], confidence=parsed[1], failed=False, attempts=attempt
                )
                break
            result = IntentResult(intent=None, confidence=None, failed=True, attempts=attempt)
            messages += [
                {"role": "assistant", "content": reply.text},
                {"role": "user", "content": f"That reply was not valid: {parsed}. Reply again."},
            ]
        self._memo[task] = result
        return result


class ClassifierEvaluation(BaseModel):
    """How well the classifier recovers the benchmark's own domain label."""

    model_config = ConfigDict(frozen=True)

    total: int
    correct: int
    failed: int
    accuracy: float
    confusions: dict[str, int]  # "true -> predicted" -> count, for wrong answers only


def evaluate_classifier(
    classifier: IntentClassifier, scenarios: Sequence[Scenario]
) -> ClassifierEvaluation:
    """Score the classifier against each scenario's domain (the true intent)."""
    correct = failed = 0
    confusions: Counter[str] = Counter()
    for scenario in scenarios:
        truth = scenario.domain.lower()
        result = classifier.classify(scenario.user_task)
        if result.failed:
            failed += 1
            confusions[f"{truth} -> (failed)"] += 1
        elif result.intent == truth:
            correct += 1
        else:
            confusions[f"{truth} -> {result.intent}"] += 1
    return ClassifierEvaluation(
        total=len(scenarios),
        correct=correct,
        failed=failed,
        accuracy=correct / len(scenarios) if scenarios else 0.0,
        confusions=dict(sorted(confusions.items())),
    )
