# D10: Seed schedule versus common random numbers

- **Status:** Accepted
- **Date logged:** 2026-11-15
- **Related:** #14

## Decision

Follow the proposal: one deterministic master sequence, permuted per cell. Store 5 seeds per scenario so the 3-to-5 seed contingency is a config change.

## Rationale

Matches the proposal; keeps cells reproducible.

## Pending / follow-up

The PRD's section 4.1 table omits D10; it is defined in `IMPLEMENTATION_PLAN.md` section 1.
