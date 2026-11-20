# D09: API call budget versus rate limit

- **Status:** Pending the pilot
- **Date logged:** 2026-11-15
- **Related:** #24, #28, #32

## Decision

Measure LLM calls per run in the pilot, then plan the frontier batch against the provider's rate limit.

## Rationale

A ReAct run makes about 5-10 calls; 1,350 frontier runs at about 7 calls is roughly 9,500 calls.

## Pilot evidence (2026-11-20)

Llama, 270 pilot runs: 5.6 model calls per run on average (4.5 with no mediator at p = 0, up to 6.7 with IBAC at p = 0.6), about 3,000 to 4,600 tokens in per run. Total estimated time for the 9 Llama cells is 9.3 hours (`docs/pilot.md`). The plan's "about 7 calls per run" estimate for the frontier model is therefore a little high for Llama; the frontier figure is still unmeasured beyond the small test below.

## Pending / follow-up

First frontier test, 2026-11-20 (`configs/pilot_frontier_grid.yaml`, 10 runs of one easy scenario, results in the gitignored `runs/pilot_frontier/`): about 2 to 3 model calls per run, about 1k tokens in and 0.2k out per run, about 2 s of model time per run. One run hit `429 You exceeded your current quota` three times within 7 seconds before succeeding on the fourth attempt, so the account's quota is a real constraint and the retry waits (2 s, 4 s, 8 s) are too short for the frontier arm. **To revisit:** the account's requests-per-minute limit, and a longer back-off for 429s. Too small a sample to extrapolate; repeat on a whole pilot cell first.

Owner: pilot (#24) and frontier-model choice (#28). Decide before the frontier batch (#32). The plan's 1,500 requests/day figure was for the Gemini free tier and must be rechecked.
