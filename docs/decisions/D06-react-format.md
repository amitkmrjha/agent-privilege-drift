# D06: ReAct format

- **Status:** Accepted
- **Date logged:** 2026-11-15
- **Related:** #17

## Decision

Text ReAct (`Thought / Action / Action Input / Observation`) parsed by our own code, for both models. Stop on `Observation:`.

## Rationale

Identical scaffold for both models; avoids provider-specific tool-call behaviour.
