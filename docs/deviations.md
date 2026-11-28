# Deviations log

What changed after the freeze (`exp-v1`), and why. The design is frozen: the pre-registration is
`prereg/preregistration.md`, and `prereg/freeze_record.json` holds the hashes of every run file.
`make freeze-check` reports any run file or registered text that differs from them.

## What goes here

- Any change to a **run file** after the tag (agent, prompt, parser, failure injector, mediators,
  model client, runner, telemetry, data and schema code, `configs/grid.yaml`, `configs/models.yaml`,
  `configs/intents.yaml`, `configs/policies/*`, `configs/tiers/*`, the frozen subset and seeds, the
  dependency lock).
- Any re-run of a cell, a lever pulled beyond the pre-declared order (D31), a model swap, or a
  change to the registered text.
- A change to the **analysis code** is only noted here; it does not change the experiment.

For each entry: the date, what changed, why, which cells and analyses it affects, and that those
analyses are now labelled **exploratory**.

Not a deviation: a registered cell that is not finished by the deadline is reported as "not run"
under the rule written in the pre-registration (section 1) and D31; mention it in the results report.

## Log

| Date | What changed | Why | Cells and analyses affected | Now exploratory |
|---|---|---|---|---|
| 2026-11-21 | Gemini quota stop and resume: the frontier lane stopped at 13:41 when the provider asked for a 19.3 h wait (daily quota), and was resumed at 13:53 after the limit was raised. | Provider limit, not a design change. | `frontier_p0.6_none` (one run was redone from its start); no run file changed. | No |
| 2026-11-21 | Amendment exp-v2 (D32): added the `frontier_large` model, 9 cells and a three-lane run plan, after the exp-v1 results were seen. Registered in section 10A before any run of the new model; exp-v1 files otherwise unchanged. | A large frontier baseline, to answer the objection that Flash-Lite is not a frontier model. | New cells 18 to 26 only; the exp-v1 analyses are unchanged and reproduce exactly. | The amendment's analyses are labelled as in section 10A (A1 and A2; the rest exploratory). |
| 2026-11-21 | Google prepaid credits ran out (HTTP 402) at 18:17 during `frontier_large_p0.3_none` (57 of 150 runs done). Resumed at about 19:50 after a top-up, with `--first 3`; only the 93 missing runs were run. The six mediator cells of `frontier_large` were not run (budget, as allowed in section 10A). | Provider billing, not a design change; section 10A already says an unfinished registered cell is reported as "not run". | `frontier_large_p0.3_none` (93 failed attempts left no run file, so nothing was kept or edited); `frontier_large_p{0,0.3,0.6}_{ibac,mac}` not run. | No. A1 and A2 use only the two finished cells. |
| 2026-11-27 | Review of the thesis analyses. Added exploratory analyses not in the pre-registration: the violation rate pooled over calls (DiD +6.4 points, bootstrap interval -0.0 to +12.8, against the registered +1.0), a split of task success by whether a risk call was proposed, and a refit of the RQ3 model with baselines (model only, previous violation) and without the 'blocked' signal. Thesis wording was narrowed: the first research question is interpreted for the models tested only (one open-weight model, two models from one provider). | The review showed that the registered per-call, per-run measure and the pooled measure can differ, and that gate cost and the RQ3 ranking need baselines. | No run file, registered text or registered analysis changed. `make freeze-check` passed. New analyses read `runs/` only. | Yes, all new analyses |
| 2026-11-28 | Gap wording narrowed after the benchmark paper was read in full. ToolPrivBench already makes the first call to each lower-privilege tool fail, and it reports that this raises escalation (Yang et al., 2026). The proposal's statement that no study treats tool failure as a variable is replaced by a narrower one: no study found varied the rate of random failure or tested gates under it. The thesis also no longer compares the p = 0 rate with a figure of about 35 per cent, because the paper reports 2.6 to 64.9 per cent over eleven models (55.9 per cent for Llama 3.1 8B) under its own protocol. | Reading the paper in full showed that the proposal's description of the benchmark was incomplete. | Thesis text only (abstract, Chapters 1, 2, 3, 4, 5, 6). The research questions, objectives, design and results are unchanged. | No |
