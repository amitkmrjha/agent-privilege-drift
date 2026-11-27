# D09: API call budget versus rate limit

- **Status:** Accepted by the author (2026-11-21): the pilot is done and the frontier lane is planned against the quota as described below (the 429 retry, the two lanes and the cut from the end, D31). The account's actual limits are read at run time, from AI Studio's rate-limit page. Earlier status: Pending the pilot
- **Date logged:** 2026-11-15
- **Related:** #24, #28, #32

## Decision

Measure LLM calls per run in the pilot, then plan the frontier batch against the provider's rate limit.

## Rationale

A ReAct run makes about 5-10 calls; 1,350 frontier runs at about 7 calls is roughly 9,500 calls.

## Pilot evidence (2026-11-20)

Llama, 270 pilot runs: 5.6 model calls per run on average (4.5 with no mediator at p = 0, up to 6.7 with IBAC at p = 0.6), about 3,000 to 4,600 tokens in per run. Total estimated time for the 9 Llama cells is 9.3 hours (`docs/pilot.md`). The plan's "about 7 calls per run" estimate for the frontier model is therefore a little high for Llama; the frontier figure is still unmeasured beyond the small test below.

## How a 429 is handled (2026-11-21)

Google does not publish the free tier's per-minute and per-day limits for this model; they are assigned per project and visible only in AI Studio's rate-limit page, and the free tier also lets Google use prompts and responses to improve its products (the paid tiers do not). Rather than wait for the numbers, the harness now retries a 429 in place:

- **Staggered, exponential, then fixed.** The same request (same messages, same seed) is retried; the wait is 15 s, 30 s, 60 s, 120 s, then fixed at 120 s, each spread by +/- 25 % so retries do not land together; a wait the provider asks for is a minimum. Up to 8 tries per call, about 10 minutes in all. Settings are `rate_limit_retry` in `configs/models.yaml`; they only change timing, so they are safe to tune.
- **A run is not restarted** after a 429, because that would spend its earlier calls' quota again. A run that still ends rate limited is left unfinished (the next invocation redoes it).
- **A stop instead of a burn.** Two such runs in a row stop the batch with the reason in the report and the manifest; a provider that asks for more than 900 s stops it at once (a daily quota). Both resume from the missing runs.
- **Logging.** A rate-limit failure is logged to `infrastructure_errors.jsonl` with up to 1,000 characters of the message, so the quota that was hit can be read.

Still open: the account's actual limits, and moving to a paid tier by linking billing (the standard price for this model is about $0.30 per million input tokens and $2.50 per million output tokens, so the whole 1,350-run frontier lane is of the order of $1 to $6). A fixed minimum gap between calls (a throttle) is not built; add it once the limit is known.

## Pending / follow-up

First frontier test, 2026-11-20 (`configs/pilot_frontier_grid.yaml`, 10 runs of one easy scenario, results in the gitignored `runs/pilot_frontier/`): about 2 to 3 model calls per run, about 1k tokens in and 0.2k out per run, about 2 s of model time per run. One run hit `429 You exceeded your current quota` three times within 7 seconds before succeeding on the fourth attempt, so the account's quota is a real constraint and the retry waits (2 s, 4 s, 8 s) are too short for the frontier arm. **To revisit:** the account's requests-per-minute limit, and a longer back-off for 429s. Too small a sample to extrapolate; repeat on a whole pilot cell first.

Owner: pilot (#24) and frontier-model choice (#28). Decide before the frontier batch (#32). The plan's 1,500 requests/day figure was for the Gemini free tier and must be rechecked.
