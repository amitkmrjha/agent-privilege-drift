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
