# D29: Which violation measure is primary (rate per call, or violating calls per run)

- **Status:** Proposed (raised by the pilot; needs the author and the supervisor before the pre-registration)
- **Date logged:** 2026-11-20
- **Related:** D02, D11, #26, #27, #29, #37

## The question

D11 fixes the primary measure as the per-run fraction of proposed calls above the minimum tier, averaged over seeds, one value per scenario. The pilot shows that this measure and a plain count of violating calls per run answer different questions, and they do not move together under failure.

## Pilot evidence (no mediator, Llama, 10 non-frozen scenarios, 3 seeds; `runs/pilot/`)

| Failure rate | Violation rate per call (D11) | Violating calls per run | Tool calls per run | Runs with at least one violation |
|---|---|---|---|---|
| 0 | 34.7 % | 1.17 | 3.47 | 76.7 % |
| 0.3 | 34.1 % | 1.40 | 3.53 | 80.0 % |
| 0.6 | 34.5 % | 1.70 | 4.43 | 80.0 % |

- The **per-call rate is flat** while the **count per run rises** (1.17 to 1.70), because failures make runs longer and the extra calls are about as risky as the others. Neither is a result: 30 runs per cell, 10 scenarios.
- "Any violation in the run" is **nearly saturated** at 77 % to 80 % already at p = 0, so it has almost no room to show an effect. It should not be primary.
- About 3.9 % of calls repeat the previous tool right after it succeeded (the canned tool replies never show the model that the job is done). Dropping them moves the overall violation share from 41.1 % to 42.0 %, so they are not driving the pattern; they are a limitation of the stub tools.

## Options

1. **Keep the per-call rate as primary (D11), add the count per run as a pre-registered secondary.** The rate measures how risky each tool choice is, whatever the run length; the count measures total exposure. Report both and explain why they can differ.
2. **Make the count per run primary.** It rises with failure pressure, but part of that rise is just longer runs, so it would partly measure persistence, not privilege choice.
3. **Keep only the per-call rate.** Simplest; leaves the longer-runs question unanswered.

## Recommendation

Option 1. Choose it on measurement grounds (what each number means), and state the reason in the pre-registration. It must **not** be chosen because one measure shows an effect in the pilot: that would be selecting the outcome after seeing the data. Both measures are computable from the existing telemetry (`violations`, `total_calls`), so adopting option 1 needs no code change beyond adding the count to the RQ1 report.

## Pending / follow-up

Decide in #26; write the choice and the reason into the pre-registration (#29). The power analysis (#27) should be run for the primary measure chosen here.
