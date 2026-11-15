# D07: Retry policy and step cap

- **Status:** Accepted (cap value pending pilot)
- **Date logged:** 2026-11-15
- **Related:** #17, #24

## Decision

The agent decides whether to retry; the harness adds no automatic retries. Hard max-steps cap suggested at 15, to be pre-registered.

## Rationale

Retry behaviour under failure is the object of RQ1.

## Pending / follow-up

Confirm 15 is not binding using the pilot (#24). Note: ToolPrivBench's own simulator defaults to `max_turns=5`, so our cap differs from the paper's setting.
