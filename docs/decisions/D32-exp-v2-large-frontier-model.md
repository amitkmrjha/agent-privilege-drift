# D32: Amendment exp-v2: add a large frontier model (Gemini 4 Carbon), after the exp-v1 results

- **Status:** Proposed by the author (2026-11-21), to be accepted at the exp-v2 freeze. Supervisor's written agreement still to be obtained (and attached to the thesis appendix).
- **Date logged:** 2026-11-21
- **Related:** #28, #30, D20, D28, D30, D31, `prereg/preregistration.md` section 10A

## What is decided

1. The registered experiment (`exp-v1`: 2 models x 3 failure rates x 3 mediators, 2,700 runs) is **complete and unchanged**. Its results stand as registered, and the primary test (H1, Flash-Lite against Llama) is reported as registered.
2. A third model, `frontier_large` = `gemini/gemini-4-carbon`, is added as an **amendment** (`exp-v2`), with its own 9 cells (numbers 18 to 26), run in the same priority order as the other lanes. The first three cells (no mediator, p = 0, 0.6, 0.3; 450 runs) are the planned run; the six mediator cells run only if time and budget allow, and a cell not finished is reported "not run".
3. The amendment's analysis is two difference-in-differences contrasts of the same form as H1 (no mediator, change from p = 0 to p = 0.6): large against Llama, and large against Flash-Lite. Each is judged at alpha = 0.025 (two tests). Everything else about the new model is exploratory.

## Why

The first model objection an examiner will raise is that `gemini-3.5-flash-lite` is not a frontier model. A large model is the direct answer. It is added after the exp-v1 results were seen (Flash-Lite and Llama rose by 8.1 and 7.1 points, difference +1.0 point, interval -4.6 to +6.6), so the amendment cannot be called blind, and it says so. Treating it as a new, separately registered stage is the honest alternative to rewriting the original registration.

## Why this model

`gemini-2.5-pro` is not available to the account (404, "no longer available to new users"). Of the models the key can call, `gemini-4-carbon` is a current model with a pinned, non-preview id (the D28 rule), the largest of its family according to secondary sources (these are not relied on), and it accepts the shared decoding settings (temperature 0.2, top-p 0.9), so it is the one frontier arm that runs with the same decoding as Llama. Its identity was confirmed from the API's model metadata (display name, 1M-token input, thinking model). Price and ranking were taken from articles and are not part of the design.

## What changes in the repo (and what does not)

- `configs/models.yaml`: new entry `frontier_large`. `configs/grid.yaml`: the model is appended, so cells 0 to 17 keep their numbers. `prereg/seed_schedule.json` is regenerated for 27 cells; cells 0 to 17 and the seed pool are **byte-identical** to exp-v1 (checked).
- `scripts/run_plan.py`: a third lane, `--first N`. `scripts/analyse.py --models ...`: the registered analysis is the default pair (`llama,frontier`) and reproduces the exp-v1 numbers exactly; the amendment contrasts are run separately.
- The freeze record gains the new model id. The exp-v1 record is kept as `prereg/freeze_record_exp-v1.json`.

## Consequences

- The thesis reports exp-v1 as registered and the amendment as a clearly labelled extension chosen after the main results.
- Gemini 4 Carbon is a thinking model; it may use many output tokens. A small harness test (3 runs) measures cost and speed before the full lane.
- No model fingerprint is recorded for Gemini; the model id and the commit in each manifest are the record (D28).
