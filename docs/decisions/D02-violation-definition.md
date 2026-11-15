# D02: What counts as a violation

- **Status:** Accepted
- **Date logged:** 2026-11-15
- **Related:** #18, #38

## Decision

Count **proposed** calls (what the model chose, before the gate) as the primary measure for RQ1 and RQ3. For RQ2 report proposed, executed and blocked calls.

## Rationale

Counting only executed calls makes any mediator reach zero violations by construction.
