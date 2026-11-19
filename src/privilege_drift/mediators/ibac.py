"""IBAC: intent-based access control, the intervention under test (decision D27).

At the start of a run the classifier reads the user's task once and names its intent. For the
rest of the run a call is allowed when the called tool's tier is at or below the highest tier
that intent may use, according to ``configs/policies/ibac_policy.yaml``. If the classifier fails,
the most restrictive policy applies (D13) and the telemetry records ``classifier_failed``.
"""

from __future__ import annotations

from collections.abc import Mapping
from functools import cache
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from privilege_drift.data.errors import DataError
from privilege_drift.mediators.base import Intent
from privilege_drift.mediators.classifier import IntentClassifier, IntentResult, Taxonomy
from privilege_drift.schema import Decision, Scenario, Tier, Tool, ToolCall

DEFAULT_POLICY_PATH = Path("configs/policies/ibac_policy.yaml")


class IntentPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    max_tier: Tier

    @field_validator("max_tier", mode="before")
    @classmethod
    def _parse_tier(cls, value: object) -> Tier:
        return Tier.parse(value)


class IbacPolicy(BaseModel):
    """The highest tier each intent may use, and the policy used when classification fails."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    intents: Mapping[str, IntentPolicy]
    fallback: IntentPolicy

    @field_validator("fallback")
    @classmethod
    def _fallback_is_most_restrictive(cls, value: IntentPolicy) -> IntentPolicy:
        if value.max_tier != min(Tier):
            raise ValueError("the fallback must allow only the lowest tier (D13)")
        return value


def load_ibac_policy(path: Path | str = DEFAULT_POLICY_PATH) -> IbacPolicy:
    try:
        return IbacPolicy.model_validate(yaml.safe_load(Path(path).read_text()))
    except (OSError, yaml.YAMLError, ValidationError) as exc:
        raise DataError(f"cannot load IBAC policy {path}: {exc}") from exc


@cache
def default_policy() -> IbacPolicy:
    return load_ibac_policy()


def _tiers_up_to(top: Tier) -> frozenset[Tier]:
    return frozenset(t for t in Tier if t <= top)


class IbacMediator:
    """Classifies in ``start_run`` and gates on the resulting intent.

    The ``intent`` argument of ``gate`` is ignored: this mediator holds the intent it classified
    itself. ``classification`` exposes the result so the telemetry can log it.
    """

    def __init__(
        self, classifier: IntentClassifier, policy: IbacPolicy, taxonomy: Taxonomy
    ) -> None:
        if set(policy.intents) != set(taxonomy.names):
            raise ValueError(
                "policy and taxonomy list different intents: "
                f"{sorted(set(policy.intents) ^ set(taxonomy.names))}"
            )
        self._classifier = classifier
        self._allowed = {name: _tiers_up_to(p.max_tier) for name, p in policy.intents.items()}
        self._fallback = _tiers_up_to(policy.fallback.max_tier)
        self.classification: IntentResult | None = None
        self._tools: dict[str, Tool] = {}

    def start_run(self, scenario: Scenario) -> None:
        self._tools = {t.name: t for t in scenario.tools}
        self.classification = self._classifier.classify(scenario.user_task)

    def gate(self, call: ToolCall, intent: Intent | None) -> Decision:
        result = self.classification
        if result is None:
            return Decision(allow=False, reason="IBAC: no run started")
        tool = self._tools.get(call.name)
        if tool is None:
            return Decision(
                allow=False, reason=f"IBAC: {call.name!r} has no label in this scenario"
            )
        tier = tool.tier.name.lower()
        if result.failed or result.intent is None:
            allowed, who = self._fallback, "classifier_failed, most restrictive policy"
        else:
            allowed = self._allowed[result.intent]
            who = f"intent {result.intent} (confidence {result.confidence:.2f})"
        verdict = "allows" if tool.tier in allowed else "does not allow"
        return Decision(allow=tool.tier in allowed, reason=f"IBAC: {who} {verdict} tier {tier}")
