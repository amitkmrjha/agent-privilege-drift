# D12: How AgentDojo is integrated

- **Status:** Accepted (only if AgentDojo is kept)
- **Date logged:** 2026-11-15
- **Related:** #23

## Decision

Custom pipeline element; the failure injector wraps AgentDojo's tool runtime.

## Rationale

AgentDojo has its own pipeline; the docs show `BasePipelineElement` and `FunctionsRuntime` as the extension points.

## Pending / follow-up

Confirm in the AgentDojo spike (#23) that a local Ollama model works via `LOCAL` or `OPENAI_COMPATIBLE`.
