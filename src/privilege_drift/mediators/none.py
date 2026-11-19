"""The no-mediator arm: every call is allowed."""

from __future__ import annotations

from privilege_drift.mediators.base import Intent
from privilege_drift.schema import Decision, Scenario, ToolCall

REASON = "no mediator: all calls allowed"


class NoneMediator:
    """Baseline arm. It still goes through the same gate, so telemetry is identical."""

    def start_run(self, scenario: Scenario) -> None:
        return None

    def gate(self, call: ToolCall, intent: Intent | None) -> Decision:
        return Decision(allow=True, reason=REASON)
