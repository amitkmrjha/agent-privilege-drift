# D20: Run the open model first, repeat with the frontier model later

- **Status:** Accepted
- **Date logged:** 2026-11-15
- **Related:** #12, #28, #29, #31, #32

## Decision

Build and run the whole grid on the open model (Llama 3.1 8B via native Ollama) first. The frontier arm is run afterwards, as a repeat of the same grid, once a frontier model and API key are chosen.

## Rationale

The open model costs nothing, has no rate limit, and its digest can be recorded; this lets the harness be debugged and the Llama batch finished before any paid calls.

## Pending / follow-up

- **The pre-registration (#29) must describe the frontier arm and its analysis before any full run**, even though the frontier batch runs later. Otherwise the frontier results are exploratory, not confirmatory.
- The frontier model choice (#28) must be fixed in the pre-registration and the model version pinned.
- Frontier API calls can be blocked or filtered by the provider. Record the finish reason on every call (`LLMResult.finish_reason`) and report blocked or filtered responses as their own count, not as normal outcomes.
- If the frontier arm cannot run, drop it with reduction lever L3 and log it in the deviations log.
