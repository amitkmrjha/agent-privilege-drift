# D19: Which tools receive injected 503s

- **Status:** Proposed (open question)
- **Date logged:** 2026-11-15
- **Related:** #16

## Decision

ToolPrivBench's own `first_attempt_fail` strategy fails every standard tool once and never fails a risk tool. The PRD instead injects HTTP 503 at probability p. Proposed: inject at rate p on tool calls regardless of tier, using the neutral 503 text, and treat the benchmark's `simulation_error` strings as an optional variant.

## Rationale

If risk tools never fail, escalation is always rewarded, which would bias RQ1 upwards.

## Pending / follow-up

Open question: should risk tools also be able to fail? Decide in #16 and confirm in #26.
