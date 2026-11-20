# D31: Which cells are run, and in what order

- **Status:** Proposed (the plan below needs the supervisor's agreement, because it changes what RQ2 can say; the fall-back is the full grid)
- **Date logged:** 2026-11-21
- **Related:** #26, #29, #30, #31, #32, D09, D20, D26, D27, D28, D30, `docs/pilot.md`, `docs/power.md`

## Why

The full grid is 18 cells and 2,700 runs (1,350 Llama, about 9.3 hours; 1,350 frontier, limited by an unresolved API quota). The author wants fewer runs and less experiment time. The deadline in the PRD is 2026-12-02.

## The primary contrast sets the floor

The pre-registered primary contrast is the difference in differences between the two models under **no mediator**, so it needs four cells: no mediator at the lowest and highest failure rate for both models. Every cut below keeps those four cells. Page's trend needs a third failure rate in the no-mediator cells; RQ2 needs the mediator cells.

## Decision (proposed): plan A+C, 9 of the 18 cells, 1,350 runs

Run these cells (ids as printed by `make list-cells`), each with 3 seeds (D30), 150 runs:

| Model | Mediator | Failure rates | Cells |
|---|---|---|---|
| llama | none | 0, 0.3, 0.6 | `llama_p0_none`, `llama_p0.3_none`, `llama_p0.6_none` |
| llama | ibac | 0, 0.3, 0.6 | `llama_p0_ibac`, `llama_p0.3_ibac`, `llama_p0.6_ibac` |
| frontier | none | 0, 0.3, 0.6 | `frontier_p0_none`, `frontier_p0.3_none`, `frontier_p0.6_none` |

**Not run** (9 cells): Llama MAC (3), frontier MAC (3), frontier IBAC (3). The grid file stays as it is (18 cells, so the cell numbers and the frozen seed schedule are unchanged); a cell that is not in this list is simply not run. The pre-registration lists the run cells and says so.

### What it costs, from the pilot's per-cell times

| | Runs | Llama time |
|---|---|---|
| Full grid | 2,700 | 9.3 h |
| Plan A+C | 1,350 | 6.0 h (none 2.7 h + IBAC 3.3 h) |

### What each question can still say

- **RQ1** (Llama vs frontier, failure pressure): complete: both models, three failure rates, no mediator. This includes the primary contrast and Page's trend.
- **RQ2** (mediators): Llama only, IBAC against no mediator, at three failure rates, with the utility floor against no mediator. **IBAC against MAC is not tested.** On ToolPrivBench the two make identical decisions by construction (D27), so this loses no real information, but it does mean the proposal's "IBAC vs MAC" contrast is not run; the supervisor must agree.
- **RQ3** (which signals predict escalation): fitted on all calls from the cells that were run.

## Run order (priority first, so a deadline cannot cost the key results)

1. The four primary cells: `llama_p0_none`, `llama_p0.6_none`, `frontier_p0_none`, `frontier_p0.6_none`.
2. The remaining no-mediator cells: `llama_p0.3_none`, `frontier_p0.3_none`.
3. IBAC: `llama_p0_ibac`, `llama_p0.6_ibac`, `llama_p0.3_ibac`.

Each cell is resumable, so a batch can be stopped and restarted. **Rule for the pre-registration:** a cell on this list that is not finished by the deadline is reported as "not run", not silently dropped, and the analyses that need it say so.

## If the supervisor does not agree

Run the full grid in the same priority order, with the MAC and frontier mediator cells last (steps 1 and 2 above, then Llama IBAC, then Llama MAC, then frontier IBAC and MAC), and cut from the end if time runs out.

## Other levers kept in reserve (not adopted)

Run Llama IBAC only at failure rates 0 and 0.6 (saves 150 runs, about 1 hour); the six no-mediator cells only (900 runs, about 2.7 hours Llama, drops RQ2); the four primary cells only (600 runs, about 1.9 hours Llama, drops Page's trend, RQ2 and most of RQ3). Fewer than 3 seeds, fewer scenarios, or a lower step cap are not recommended (D30, D07).

## Pending / follow-up

Supervisor agreement (RQ2 framing, this plan). Then write the run cells and the not-run rule into the pre-registration (#29), before the freeze (#30). Frontier runs also wait on the quota (D09) and the model choice (D28).
