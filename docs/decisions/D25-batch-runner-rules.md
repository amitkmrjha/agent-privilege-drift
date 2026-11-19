# D25: How the batch runner resumes, retries and checks

- **Status:** Proposed (the integrity-check change departs from the plan; pre-register it in #29)
- **Date logged:** 2026-11-19
- **Related:** #21, #22, #24, #29, D03, D09, D21, D22, D23

## Decision

1. **Cells are numbered by the grid order.** `configs/grid.yaml` lists models, rates and mediators; the cell number is `(model_idx * n_rates + rate_idx) * n_mediators + mediator_idx`. The frozen seed schedule is indexed by that number (D21), so the order is fixed once pre-registered. Removing an entry (reduction levers L1, L3) renumbers the cells after it, and the schedule must be regenerated for the new grid.
2. **Names are deterministic.** Cell id `llama_p0.3_none`; run id `<cell id>__<scenario id>__s<seed idx>`; result files `runs/<cell id>/<run id>.jsonl` (and `.raw.jsonl`).
3. **Resume rule: a run is finished if its result file exists and parses as that run.** Files are written atomically and the main file is renamed last, so a killed batch leaves a whole file or none. The plan says "passes its checksum"; a successful parse of the whole file is the simple version of that, and a corrupted file is simply redone.
4. **Infrastructure errors are retried, logged apart and never become data.** Timeouts, 429/5xx and connection errors (`LLMCallError`) are retried with doubling back-off (4 tries, 2 s first wait). Every failed attempt is appended to `runs/<cell id>/infrastructure_errors.jsonl`. A run that still fails is left without a result file and is listed as unfinished in the manifest; the next invocation tries it again. A missing API key stops the whole batch. A retried run starts again from its first step, so it sees the same failure draws.
5. **One worker, no rate limiting yet.** The cell runs its items one after another, which is what Llama needs. A requests-per-minute limit for the frontier arm depends on the pilot (D09), so it is added in #32 when the real limit is known.
6. **The manifest** (`manifest.json` per cell) records the config hash, git commit and whether the tree was dirty, the model digest(s) seen (more than one means the model changed mid-cell), the seeds used, counts, times and status (`complete` or `incomplete`).
7. **Integrity checks, with one change from the plan (7.8).**
   - *All runs present:* every planned run has a valid result and there are no other result files (150 per cell).
   - *Injection replay (replaces "empirical rate within +/-3 points of p"):* every call's `injected` flag must equal what the injector's draw says. The draws are a fixed function of the run key (D22), so the check recomputes each one. The plan's band is under two standard deviations wide for a few hundred draws, so a correct cell would fail it about one time in ten; the replay never fails by chance and catches any single wrong call. The empirical rate is still printed.
   - *Tier attribution:* each call's tier, the scenario's minimum tier and the violation flag match the scenario, and each summary's violation count matches its calls.

## Rationale

Each rule keeps the batch restartable without supervision and keeps infrastructure trouble out of the behavioural data.

## Pending / follow-up

- All three arms are registered in `default_mediators(llm)` (MAC in #19, IBAC in #20). An unknown mediator name stops the cell with "not implemented yet".
- The real throughput table comes from the pilot (#24).
- The CLI is `privilege-drift run-cell <cell id> [--limit N]` and `check-cell <cell id>` (also `make run-cell CELL=...`). Running a whole cell calls the model for hours; nothing runs it unasked.
