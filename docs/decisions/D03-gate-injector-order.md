# D03: Order of mediator gate and failure injector

- **Status:** Accepted
- **Date logged:** 2026-11-15
- **Related:** #15, #16

## Decision

`agent -> mediator gate -> failure injector -> tool`. A blocked call never reaches the tool, so it gets no 503 draw.

## Rationale

Keeps injected failures independent of the access decision.
