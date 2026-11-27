# D30: Seeds per scenario (3 or 5)

- **Status:** Accepted: keep 3 seeds (the author chose the option that simplifies the run and cuts experiment time, 2026-11-20). The plan's rule pointed to 5; this is a documented departure from it, with the consequences below.
- **Date logged:** 2026-11-20
- **Related:** #26, #27, #29, D10, D29, `docs/power.md`

## The question

`configs/grid.yaml` runs 3 seeds per scenario; the frozen seed schedule already holds 5 (D10), so moving to 5 is one number. The plan (issue #27) says: simulate the study, and if power for a 12-point difference is below 80 %, use 5 seeds.

## Evidence (`docs/power.md`, generated from the pilot; 10,000 simulated studies per row)

Power to detect a true 12-point difference in violation rate, 50 scenarios, paired Wilcoxon on scenario means, noise estimated from the pilot:

| Contrast | Seeds | Power at 0.05 | Power at 0.05/18 (Holm stand-in) |
|---|---|---|---|
| Plain two-cell comparison | 3 | 97.0 % | **76.5 %** |
| Plain two-cell comparison | 5 | 99.8 % | 96.5 % |
| **Primary: difference in differences (four cells)** | 3 | **78.7 %** | 35.8 % |
| **Primary: difference in differences (four cells)** | 5 | 94.2 % | 66.2 % |

Smallest difference reached with 80 % power at the 0.05 level: for the primary contrast 12.2 points with 3 seeds and 9.5 points with 5. The simulation's false-positive rate with no true difference is 5.0 % to 5.1 % at the 0.05 level, as it should be.

## Reading it

- With 3 seeds the plan's rule is triggered twice: the plain comparison at the strict level (76.5 %) and the primary contrast at 0.05 (78.7 %) are both just below 80 %. The primary contrast is the weaker design because it compares four cells, so it carries about twice the noise.
- The noise estimate is rough: 10 pilot scenarios, and the run-to-run noise came out at its floor (no noise beyond counting error). If the true run-to-run variance is twice the estimate, 5 seeds give 71 % for the primary contrast at 0.05, so even 5 seeds is not a guarantee.
- The pilot's per-call violation rate looked flat across failure rates (D29). If the true effect is below 12 points, power is lower than shown; the study can then report only an upper bound ("any effect is smaller than about 9.5 points"), which is still a defensible result.
- The analysis assumes the per-call rate is the primary measure. If D29 chooses another, the simulation should be re-run for it.

## Cost of 5 seeds

900 more runs per model (450 per extra seed per model), so 67 % more time and calls. At the pilot's speed the full Llama grid goes from about 9.3 hours to about 15.5 hours. For the frontier arm the extra calls count against the quota (D09), which is still unresolved.

## Options

1. **5 seeds (recommended).** Follows the plan's rule; the primary contrast then reaches 94 % at 0.05. Costs the extra hours and quota above.
2. **Stay at 3 seeds.** Saves a third of the time, but the primary contrast is under-powered for a 12-point effect, and the smallest effect it can detect at 80 % power is 12.2 points. State that limit up front.
3. **5 seeds for Llama only.** The frontier arm is the one limited by quota. `seeds_per_scenario` is a single number for the whole grid today, so this needs a small grid change before the freeze, and the two arms would then be averaged over different numbers of seeds.

## Decision

**Keep `seeds_per_scenario: 3`** in `configs/grid.yaml`. Nothing in the configuration changes. This saves 900 runs per model against 5 seeds: the Llama grid stays at about 9.3 hours instead of about 15.5, and the frontier arm uses a third fewer calls against its unresolved quota (D09).

## What this means for the study (to carry into the pre-registration, #29, and the thesis)

- **The primary contrast is borderline for a 12-point effect:** 78.7 % power at the 0.05 level, just under the plan's 80 %, and it can detect about 12.2 points with 80 % power. State this limit up front, not after the results.
- **Test the primary contrast at 0.05 as one pre-registered test.** At the stricter Holm stand-in level (0.05/18) its power is only 35.8 %, so putting it inside the 18-test family would leave it unable to detect a 12-point effect. The plain two-cell comparisons are then secondary (76.5 % at the strict level).
- **A non-significant primary result is reported as an upper bound** ("any difference is smaller than about 12 points"), never as "no effect". If the run-to-run noise is higher than the pilot suggests (twice the estimate), power for the primary contrast falls to about 50 %.
- **The option to add seeds is kept.** The frozen seed schedule already holds 5 seeds per scenario (D10). If the pre-registration states in advance that seeds 4 and 5 will be added when the primary result is inconclusive, the extension is a planned step, not a deviation. That rule is not adopted here; decide it in #29 if wanted.
- Re-run `scripts/power_analysis.py` if D29 changes the primary measure.
