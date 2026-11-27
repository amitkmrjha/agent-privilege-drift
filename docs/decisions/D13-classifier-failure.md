# D13: IBAC classifier failure

- **Status:** Accepted
- **Date logged:** 2026-11-15
- **Related:** #20

## Decision

If classification fails after one retry, fall back to the most restrictive policy and log `classifier_failed`.

## Rationale

Fail closed; the failure is recorded so it can be reported.
