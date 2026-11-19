# D19: Which tools receive injected 503s

- **Status:** Proposed (open question)
- **Date logged:** 2026-11-15
- **Related:** #16

## Decision

ToolPrivBench's own `first_attempt_fail` strategy fails every standard tool once and never fails a risk tool. The PRD instead injects HTTP 503 at probability p. Proposed: inject at rate p on tool calls regardless of tier, using the neutral 503 text, and treat the benchmark's `simulation_error` strings as an optional variant.

## Rationale

If risk tools never fail, escalation is always rewarded, which would bias RQ1 upwards.

## Implementation note (#16)

Built as proposed: `FailureInjector` makes one draw per call that reaches it and never looks at the tool's tier, so risk tools fail at the same rate p as standard tools. The text is one constant, `FIXED_503_BODY`, the same for every tool and model. The benchmark's own `simulation_error` strings are not used. A test checks that every tier can fail.

Two consequences to keep in mind:
- A call to a tool the scenario does not offer also gets a draw, so it can come back as a 503 instead of a 404. The telemetry marks the result as injected.
- Calls blocked by the mediator get no draw (D03).

## Pending / follow-up

Still needs the author's confirmation: should risk tools also be able to fail? Confirm in #26. Changing the answer later means changing the injector, so it must be settled before the pre-registration.
