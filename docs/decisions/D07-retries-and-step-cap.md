# D07: Retry policy and step cap

- **Status:** Accepted by the author (2026-11-21), as recommended, before the freeze. Earlier status: Accepted (cap value pending pilot)
- **Date logged:** 2026-11-15
- **Related:** #17, #24

## Decision

The agent decides whether to retry; the harness adds no automatic retries. Hard max-steps cap suggested at 15, to be pre-registered.

## Rationale

Retry behaviour under failure is the object of RQ1.

## Pilot evidence (2026-11-20, `docs/pilot.md`, 270 runs, Llama, 10 non-frozen scenarios)

- All 270 runs ended with a Final Answer; none hit the cap.
- Model calls per run: mean 5.6, 95th percentile 9.5, maximum 15. 11 runs used more than 10 calls, and one used all 15, so the cap was not binding but the longest run sat exactly on it.

**Recommendation:** keep 15. The pilot does not show it binding. Expect a few runs to reach it in 1,350, and report the max-steps rate as a health measure (the plan's threshold is about 5 %); raise the cap only if the real runs exceed it. It stays Proposed until confirmed in #26.

## Pending / follow-up

Note: ToolPrivBench's own simulator defaults to `max_turns=5`, so our cap differs from the paper's setting. Confirm 15 for the pre-registration (#26, #29).

## Accepted 2026-11-21

Decision: the step cap is **15** for the pre-registration.
