# D16: Ollama runs natively, not in Docker

- **Status:** Accepted (done)
- **Date logged:** 2026-11-15
- **Related:** PR #50

## Decision

Use the native Ollama install. The harness container reaches it via `host.docker.internal:11434`.

## Rationale

Docker on macOS has no GPU access, so a containerised model would be slower and would make recorded latency differ from native runs.

## Pending / follow-up

Record the native Ollama version (0.40.16 at the time of writing) and model digest in the pre-registration.
