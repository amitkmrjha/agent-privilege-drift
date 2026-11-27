# Results of the exp-v2 amendment (large frontier model)

Source: `make analyse-v2` (large model against Llama: 1,818 runs; against Flash-Lite: the matching set). The 1,818
are Llama's 1,350, the large model's 450 no-mediator runs, and 18 smoke-test runs of one scenario
(`BIZ-AUTH-016`, 3 seeds) in each of the six large-model mediator cells. The smoke runs are not part of the
two tests below, which use the no-mediator cells only. Registered in
`prereg/preregistration.md` section 10A before any run of the new model, **after the exp-v1 results were
seen**. The large model is `gemini/gemini-4-carbon`, temperature 0.2, top-p 0.9.

## What ran

| Cells | Runs | State |
|---|---|---|
| `frontier_large_p{0, 0.3, 0.6}_none` | 450 | Finished; `check-cell` PASS for all three |
| `frontier_large_p{0, 0.3, 0.6}_{ibac, mac}` | 900 | **Not run** (budget), apart from the 3 smoke-test runs of one scenario in each cell. Reported as "not run", as section 10A allows; those 18 runs are not analysed as results |

Run record: the lane stopped once when the provider's prepaid credits ran out (see `docs/deviations.md`).
No run file was changed.

## Violation rate per call, no mediator

| p | Llama 3.1 8B | Gemini 3.5 Flash-Lite | gemini-4-carbon |
|---|---|---|---|
| 0 | 30.8% | 2.3% | 0.0% |
| 0.3 | 30.8% | 4.0% | 0.0% |
| 0.6 | 37.9% | 10.4% | 0.4% |

## The two amendment tests (alpha 0.025 each)

Change from p = 0 to p = 0.6, no mediator, 50 scenarios, bootstrap interval and paired Wilcoxon.

| Test | Difference in differences | 95% interval | p (Wilcoxon) | Cliff's delta | Cohen's dz |
|---|---|---|---|---|---|
| A1: large minus Llama | -6.7 points | [-12.3, -0.9] | 0.0040 | -0.34 (medium) | -0.33 |
| A2: large minus Flash-Lite | -7.7 points | [-10.3, -5.0] | < 0.0001 | -0.51 (large) | -0.80 |

Reading: both are below 0.025. The large model's rise under failure pressure is +0.4 points, against +7.1
(Llama) and +8.1 (Flash-Lite). For A2 the interval lies inside the 12-point target. For A1 the interval
reaches -12.3, so a difference as large as the target is not ruled out.

## Limits to state with these results

- The large model starts at 0%, so there is little room to rise (a floor effect). The tests compare absolute
  points; the result says the pressure effect is small in this model, not that it is zero in general.
- The model was chosen after the exp-v1 results were seen. H1 stays the registered primary test and is
  unchanged (null result).
- Everything else about the large model is exploratory. There are no mediator results for it, so RQ2 for the
  large model is untested.
- Price and ranking of the model come from secondary sources. Gemini gives no model fingerprint; the model
  id, date and commit are the record.
