# D09: API call budget versus rate limit

- **Status:** Pending the pilot
- **Date logged:** 2026-11-15
- **Related:** #24, #28, #32

## Decision

Measure LLM calls per run in the pilot, then plan the frontier batch against the provider's rate limit.

## Rationale

A ReAct run makes about 5-10 calls; 1,350 frontier runs at about 7 calls is roughly 9,500 calls.

## Pending / follow-up

Owner: pilot (#24) and frontier-model choice (#28). Decide before the frontier batch (#32). The plan's 1,500 requests/day figure was for the Gemini free tier and must be rechecked.
