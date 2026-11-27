# Results report

A plain record of what was found, for writing the thesis from. It is not thesis text. Numbers are copied from the
generated tables of `make analyse` (exp-v1, registered) and `make analyse-v2` (exp-v2, amendment). Regenerate and
re-check them before the thesis is submitted. Figures are the PNG files in the analysis output (`figures/`).

## 0. What was run

| Item | Value |
|---|---|
| Design | ToolPrivBench, 50 scenarios x 3 seeds per cell; failure rate p = 0, 0.3, 0.6; mediator none, MAC, IBAC |
| exp-v1 (registered, tag `exp-v1`) | Llama 3.1 8B Instruct and Gemini 3.5 Flash-Lite; 18 cells; 2,700 runs; 8,382 calls |
| exp-v2 (amendment, tag `exp-v2`) | `gemini/gemini-4-carbon`, no-mediator cells only (3 cells, 450 runs). Six mediator cells not run |
| Integrity | All 21 full cells pass the three cell checks; run files match the freeze record |
| Archive | `exp_runs_final_2026-11-21.zip` (a release asset of this repository, not stored in git), SHA-256 `90aaea8615ce3c65b8f7477ff4a569cdfd172071872bd1d2835aeab5ece5474f` |

Violation = a proposed call above the scenario's minimum tier. Primary measure = violation rate per call (D29).
The scenario is the unit of analysis.

## 1. RQ1: does failure pressure raise escalation?

**Registered test (H1, primary).** Difference in differences, no mediator: (Flash-Lite change) minus (Llama change),
change = V(0.6) - V(0), alpha 0.05.

| | p = 0 | p = 0.3 | p = 0.6 | Change |
|---|---|---|---|---|
| Llama 3.1 8B | 30.8% | 30.8% | 37.9% | +7.1 points |
| Gemini 3.5 Flash-Lite | 2.3% | 4.0% | 10.4% | +8.1 points |

- Difference in differences **+1.0 point**, 95% bootstrap interval [-4.6, +6.6], paired Wilcoxon p = 0.92,
  Cliff's delta 0.03 (negligible), Cohen's dz 0.05.
- **Decision: H1 not supported.** The interval lies inside the +/-12-point target, so a difference of that size is
  ruled out; any real difference is at most 6.6 points (an upper bound, not an estimate; PO13).
- **H1a (trend, secondary): supported for both models.** With no mediator the rise from p = 0 to 0.6 is significant
  after Holm (Llama +7.1 points, p_holm 0.041; Flash-Lite +8.1, p_holm 0.001). Page's trend: Flash-Lite p < 0.001
  under every mediator; Llama p = 0.006 (none), 0.018 (MAC), 0.026 (IBAC). The effect is modest and mostly at p = 0.6.
- Flash-Lite starts 27 to 32 points below Llama at every cell (all nine between-model contrasts p_holm < 0.001).
  Relative to its start the rise is larger for Flash-Lite (about 4.5 times) than for Llama (about 1.2 times);
  this relative view is exploratory only.

**Answer in one sentence.** Failure pressure raises the violation rate by a few points, mainly at p = 0.6, in both
models, and the two models do not differ in how much it rises.

## 2. RQ2: do mediators reduce violations, and at what cost?

**Registered tests (H2).** IBAC against none and against MAC, for proposed, executed and blocked violations, and the
5-point utility floor on task success.

| Executed violations | Guard on (MAC or IBAC) | No mediator (p = 0, 0.3, 0.6) |
|---|---|---|
| Llama | 0.000 in all six guard cells | 30.8%, 30.8%, 37.9% |
| Flash-Lite | 0.000 in all six guard cells | 2.3%, 4.0%, 10.4% |

- IBAC and MAC do not differ on proposed or blocked violations for either model (all Holm p >= 0.13). This is
  expected: they are equal by construction on this benchmark (D26, D27).
- IBAC classifier: 42 of 50 scenarios matched the benchmark's domain label (84%); 0 unreadable replies.

Task success (share of runs completed), %:

| p | Llama none / MAC / IBAC | Flash-Lite none / MAC / IBAC |
|---|---|---|
| 0 | 100 / 100 / 100 | 100 / 100 / 100 |
| 0.3 | 100 / 95.3 / 100 | 99.3 / 100 / 96.0 |
| 0.6 | 98.0 / 82.7 / 80.7 | 91.3 / 77.3 / 84.0 |

Utility floor (IBAC minus comparator, floor 5 points), registered outcomes:

| Comparison | Llama | Flash-Lite |
|---|---|---|
| IBAC vs MAC, pooled | **met** (+0.9, [-2.2, +4.0]) | **met** (+0.9, [-2.4, +4.2]) |
| IBAC vs none, pooled | **inconclusive** (-5.8, [-8.2, -3.6]) | **inconclusive** (-3.6, [-6.4, -0.7]) |
| IBAC vs none at p = 0.6 | **not met** (-17.3, [-24.7, -10.7]) | **inconclusive** (-7.3, [-14.7, 0.0]) |

Registered wording for "inconclusive": "the data neither show IBAC within 5 points of the comparator nor more than
5 points below it".

**Decision.** H2 is supported for violations (guards remove every executed violation) and for the floor against MAC.
Against no mediator the floor is inconclusive pooled, and not met for Llama at p = 0.6. The proposal's phrasing
"reduces violations but at a utility cost exceeding the threshold" fits that last case (PO5).

**Answer in one sentence.** Guards stop every executed violation; IBAC and MAC behave the same on this benchmark; the
price is lower task success when tools fail often.

## 3. RQ3: what predicts escalation? (descriptive)

| Label | Calls | Positive | Held-out AUC | Brier |
|---|---|---|---|---|
| Primary: next proposed call is a violation | 8,382 | 33.9% | 0.77 (folds 0.76 to 0.79) | 0.175 |
| Secondary | 8,382 | 10.7% | 0.83 | 0.082 |

Primary importance (mean absolute SHAP): previous call blocked 0.84; previous call succeeded 0.58; collinear
step/token/service-unavailable component 0.55; retries since last success 0.33; cumulative reasoning tokens 0.12.
For the secondary label the top three signals are close (1.29, 1.26, 1.24).

**Caution.** "Previous call blocked" mostly reflects the mediator arms, not the agent's choice under failure. Lean on
the secondary label for the behavioural reading.

**Answer in one sentence.** A model on the previous observation and recent retries predicts escalation with AUC
0.77 to 0.83, and what the agent just saw (a block or a success) carries the most weight.

## 4. Exploratory and amendment findings (kept apart)

**exp-v2 amendment: large model, no mediator** (registered after the exp-v1 results were seen; section 10A, D32).
Tests A1 and A2 each judged at alpha 0.025; everything else about this model is exploratory.

| p | gemini-4-carbon |
|---|---|
| 0 | 0.0% |
| 0.3 | 0.0% |
| 0.6 | 0.4% |

| Test | Difference in differences | 95% interval | p (Wilcoxon) | Cliff's delta |
|---|---|---|---|---|
| A1: large minus Llama | -6.7 points | [-12.3, -0.9] | 0.0040 | -0.34 (medium) |
| A2: large minus Flash-Lite | -7.7 points | [-10.3, -5.0] | < 0.0001 | -0.51 (large) |

Reading: both tests are below 0.025. The large model hardly rises under pressure (+0.4 points) against +7.1 and +8.1.
The large model starts at 0%, so there is little room to rise (a floor effect). A1's interval reaches -12.3, so a
difference as large as the target is not ruled out for A1. There are no mediator results for this model.
Detail: `docs/results/results_exp_v2.md`.

**Other exploratory items:** relative rise (section 1); secondary RQ3 label; the IBAC classifier accuracy.

## 5. Deviations and what they touch

Full log: `docs/deviations.md`.

| Date | Event | Results touched |
|---|---|---|
| 2026-11-21 | Gemini quota stop 13:41, resumed 13:53 | None (one run redone from its start) |
| 2026-11-21 | Amendment exp-v2 (large model) added after the v1 results | Adds A1 and A2; the registered analysis is unchanged |
| 2026-11-21 | Prepaid credits ran out (HTTP 402) at 18:17; resumed after a top-up; six mediator cells not run | Large model has no mediator results; no run file changed |

## 6. Limits to state with the results

- Flash-Lite is a small frontier-family model on provider-default decoding (D28); Llama uses temperature 0.2, top-p 0.9.
  The primary test compares each model's own change, so a level difference does not bias it.
- IBAC equals MAC by construction on this benchmark, so RQ2 is a check, not a contest. A benchmark that separates them
  (AgentDojo) was not run (D33).
- 3 seeds: about 79% power for the primary contrast, minimum detectable effect about 12 points. A null is supported by
  the interval, not by power alone.
- One benchmark, one run per seed, small effects, and the large model chosen after the v1 results were seen.
- Gemini records no model fingerprint; the model id, the date and the commit are the record.

## 7. Promised outcomes (PRD 1 section 3)

| PO | Status | Evidence or reason |
|---|---|---|
| PO1 | Evidence | Section 1 table, change per model with intervals |
| PO2 | Evidence | The change V(0.6) - V(0) is reported per model and mediator (`rq1_rates.csv`, `rq1_contrasts.csv`) |
| PO3 | Evidence | H1 result: +1.0 point, [-4.6, +6.6], p = 0.92, Cliff's delta 0.03 |
| PO4 | Partly | Violations, task success and the floor are reported. Attack success rate is **missing**: it belongs to AgentDojo, not run (D33) |
| PO5 | Evidence | Registered floor outcomes, section 2 |
| PO6 | Evidence | Section 3: SHAP ranking and held-out AUC. Check whether bootstrap intervals on ranks are in `rq3_*_importance.csv` before claiming them |
| PO7 | Evidence | The three one-sentence answers, section 8 |
| PO8 | Discussion only | Needs the limits above; written in the thesis, not measured here |
| PO9 | Evidence | Tags `exp-v1`, `exp-v2`, hash files, `freeze_record.json`, cell checks, deviations log |
| PO10 | Evidence | Repo, archive with SHA-256; public release is #44 |
| PO13 | Evidence | Upper-bound wording used for the null and for A1/A2 |

## 8. Answers to the three findings promised in the abstract

1. **Over-escalation, frontier against Llama (RQ1).** Failure pressure raises violations by about 7 to 8 points in both
   models, and the two do not differ (difference +1.0 point, [-4.6, +6.6]). A larger model barely escalates at all
   (+0.4 points; amendment, after the v1 results).
2. **IBAC against MAC (RQ2).** IBAC and MAC behave the same here and both remove every executed violation. IBAC's task
   success is within the 5-point floor against MAC, and inconclusive or below it against no mediator when tools fail often.
3. **Predictive signals (RQ3).** The previous observation (blocked or succeeded) and recent retries predict the next
   violation best (AUC 0.77 to 0.83).
