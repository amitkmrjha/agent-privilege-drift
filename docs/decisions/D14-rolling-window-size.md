# D14: Rolling-window size k for the 503 rate

- **Status:** Accepted by the author (2026-11-21), as recommended, before the freeze. Earlier status: Pending the pilot
- **Date logged:** 2026-11-15
- **Related:** #18, #39, #26

## Decision

k is fixed in the pre-registration.

## Rationale

Chosen from the pilot so the window is neither noisy nor lagging.

## Pilot evidence (2026-11-20, 10 non-frozen scenarios, cells with failures only)

Runs are short: the median is 4 tool calls and the 90th percentile 8. The share of calls whose window is completely full:

| k | Calls with a full window |
|---|---|
| 3 | 40.6 % |
| 5 | 16.9 % |
| 8 | 3.3 % |
| 10 | 0.9 % |

So with k = 5 or more the "rolling" rate is, for most calls, just the share of 503s so far in the run, not a recent window. I also refit the RQ3 model with each k (leave-scenario-out AUC): 0.696 for k = 3 and 0.698 for k = 5, 8 and 10. The outcome does not tell the sizes apart, and with only 10 scenarios it could not be expected to.

**Recommendation: k = 3.** It is the largest size that is a genuine recent window for a good share of calls (41 %), and it costs nothing in AUC. This is a design choice, not an evidence-driven one: the pilot shows only that larger k stops being a window. It changes `window_k` in `configs/grid.yaml` and `configs/pilot_grid.yaml` and the default in the recorder, all before the freeze; nothing is changed yet. Needs the author's confirmation in #26.

## Pending / follow-up

Confirm k in #26 before the pre-registration tag, then change the three places above.

## Accepted 2026-11-21

Decision: **k = 3**. Set in `configs/grid.yaml` and as the recorder's default. (The pilot's own grids keep 5, the value the pilot ran with.)
