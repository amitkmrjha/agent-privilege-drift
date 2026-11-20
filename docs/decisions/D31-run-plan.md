# D31: Which cells are run, and in what order

- **Status:** Accepted by the author (2026-11-21), on the supervisor's general agreement to steps that simplify the experiment while keeping it correct and defensible (relayed by the author; not yet confirmed in writing). **Plan A**, so that RQ2 keeps its original wording. Revised the same day from the earlier plan A+C (which dropped Llama's MAC cells and would have forced RQ2 to be reworded). Still open with the supervisor: what 2 December covers and the utility-floor wording. The fall-back remains the full grid.
- **Date logged:** 2026-11-21
- **Related:** #26, #29, #30, #31, #32, D09, D20, D26, D27, D28, D30, `docs/pilot.md`, `docs/power.md`

## Why

The full grid is 18 cells and 2,700 runs (1,350 Llama, about 9.3 hours; 1,350 frontier, limited by an unresolved API quota). The author wants fewer runs and less experiment time, without changing a research question. The deadline in the PRD is 2026-12-02.

## What stays fixed

- **The primary contrast** (difference in differences, no mediator) needs four cells: no mediator at the lowest and highest failure rate for both models. Every option below keeps them.
- **RQ2 as written** names three arms: none, MAC and IBAC, "across failure regimes". Plan A runs all three on Llama at all three failure rates, so RQ2 is tested exactly as the proposal states it. That IBAC and MAC behave the same on ToolPrivBench (D27) is then a result the data confirm, not a reason to reword the question.

## Decision: plan A, 12 of the 18 cells, 1,800 runs

Each cell has 150 runs (50 scenarios x 3 seeds, D30). Cell ids are those printed by `make list-cells`.

| Model | Mediator | Failure rates | Cells |
|---|---|---|---|
| llama | none | 0, 0.3, 0.6 | `llama_p0_none`, `llama_p0.3_none`, `llama_p0.6_none` |
| llama | mac | 0, 0.3, 0.6 | `llama_p0_mac`, `llama_p0.3_mac`, `llama_p0.6_mac` |
| llama | ibac | 0, 0.3, 0.6 | `llama_p0_ibac`, `llama_p0.3_ibac`, `llama_p0.6_ibac` |
| frontier | none | 0, 0.3, 0.6 | `frontier_p0_none`, `frontier_p0.3_none`, `frontier_p0.6_none` |

**Not run** (6 cells): frontier MAC (3) and frontier IBAC (3). The grid file stays as it is (18 cells, so the cell numbers and the frozen seed schedule are unchanged); a cell that is not on the list is simply not run. The pre-registration lists the run cells.

**Scope of RQ2:** it is tested on Llama. IBAC's classifier is Llama (PRD I7), the plan describes its secondary grid as "Llama only", and the frontier arm runs without mediators. This is a statement of scope, not a change to the question. **To check:** the proposal's own RQ2 sentence. If it explicitly requires both models, either add this one-line scope note or run the six frontier mediator cells (900 runs, heavy on the unresolved frontier quota).

### What it costs, from the pilot's per-cell times

| | Runs | Llama time |
|---|---|---|
| Full grid | 2,700 | 9.3 h |
| Plan A | 1,800 | 9.3 h (none 2.7 h, MAC 3.3 h, IBAC 3.3 h) |

The saving against the full grid is all in the frontier arm: 900 fewer calls-worth of runs against its unresolved quota (D09).

### What each question can say

- **RQ1** (Llama vs frontier, failure pressure): complete: both models, three failure rates, no mediator, including the primary contrast and Page's trend.
- **RQ2** (mediators): complete as written, on Llama: IBAC vs MAC vs none at three failure rates, proposed, executed and blocked violations, task success, and the utility floor against both comparators.
- **RQ3** (which signals predict escalation): fitted on all calls from the cells that were run.

## Run order (priority first, lowest-value cells last, so a deadline cannot cost the key results)

1. The four primary cells: `llama_p0_none`, `llama_p0.6_none`, `frontier_p0_none`, `frontier_p0.6_none`.
2. The remaining no-mediator cells: `llama_p0.3_none`, `frontier_p0.3_none`.
3. IBAC, the intervention, at the two ends: `llama_p0_ibac`, `llama_p0.6_ibac`.
4. MAC at the two ends: `llama_p0_mac`, `llama_p0.6_mac`.
5. The middle failure rate for the mediators: `llama_p0.3_ibac`, then `llama_p0.3_mac`.

Each cell is resumable, so a batch can be stopped and restarted. **Rule for the pre-registration:** a cell on this list that is not finished by the deadline is reported as "not run", not silently dropped, and the analyses that need it say so. If the clock forces it, the cut falls on the last cells above first, and any resulting change to what RQ2 can say is a logged deviation.

## Reductions held in reserve (not adopted; each keeps RQ2's wording)

- **A1: Llama MAC and IBAC only at failure rates 0 and 0.6** (drop the two p = 0.3 mediator cells): 1,500 runs, Llama 7.2 h. RQ2 would then compare the arms at two failure regimes instead of three. Step 5 of the run order is exactly these two cells, so A1 happens automatically if time runs out.
- **A2: A1, and the frontier only at 0 and 0.6:** 1,350 runs. The primary contrast is unaffected; the frontier arm loses its middle point for a trend. Useful if the quota is tight.
- Cells are independent, so two could run at once in two terminals. Untested, and parallel load can change a local model's output slightly even with fixed seeds, so it needs a small trial and one mode used throughout.
- Not recommended: fewer than 3 seeds (D30), fewer scenarios, or a lower step cap (D07).

## Pending / follow-up

Check the proposal's RQ2 sentence (scope note, above). Confirm the supervisor's agreement in writing. Write the run cells and the not-run rule into the pre-registration (#29), before the freeze (#30). Frontier runs also wait on the quota (D09) and the model choice (D28).
