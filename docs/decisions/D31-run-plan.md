# D31: Which cells are registered, and in what order they are run

- **Status:** Accepted by the author (2026-11-21). **Register the full 18-cell grid** and run it in a fixed priority order; if time or the frontier quota runs short, stop from the end of that order, and report the unfinished cells as "not run" under a rule written in advance (so this is a planned cut, not a deviation). The supervisor agrees in principle to simplifications that keep the design correct and defensible (relayed by the author; not yet confirmed in writing). Still open with the supervisor: what 2 December covers and the utility-floor wording.
- **History (all 2026-11-21):** first proposed 9 cells (A+C), then 12 (plan A, to keep RQ2's wording), then the full grid, because the six frontier mediator cells add little machine time and the original design needs no re-justifying. The earlier options are kept below as the pre-declared cuts.
- **Related:** #26, #29, #30, #31, #32, D09, D20, D26, D27, D28, D30, `docs/pilot.md`, `docs/power.md`

## Why

The full grid is 18 cells and 2,700 runs (1,350 Llama, about 9.3 hours of local time; 1,350 frontier, limited by an unresolved API quota). The author wants the original design kept (RQ2 as written, for both models) and will decide any mitigation later. The deadline in the PRD is 2026-12-02.

## What stays fixed

- The pre-registered primary contrast (difference in differences, no mediator) needs four cells: no mediator at the lowest and highest failure rate for both models. They are first in each lane below.
- RQ1, RQ2 and RQ3 keep the wording of the proposal, with no scope note needed.

## Decision: register all 18 cells, run them in two concurrent lanes

Each cell has 150 runs (50 scenarios x 3 seeds, D30). The two lanes use different resources (local GPU for Llama, the network for the frontier model), so they can run at the same time in two terminals; the frontier IBAC cells also call local Llama for the intent classifier, a short call per task. Within a lane, cells run in this order (highest value first):

| Order | Lane L: Llama (local, about 9.3 h) | Lane F: frontier (API, quota-bound) |
|---|---|---|
| 1 | `llama_p0_none`, `llama_p0.6_none` | `frontier_p0_none`, `frontier_p0.6_none` |
| 2 | `llama_p0.3_none` | `frontier_p0.3_none` |
| 3 | `llama_p0_ibac`, `llama_p0.6_ibac` | `frontier_p0_ibac`, `frontier_p0.6_ibac` |
| 4 | `llama_p0_mac`, `llama_p0.6_mac` | `frontier_p0_mac`, `frontier_p0.6_mac` |
| 5 | `llama_p0.3_ibac`, `llama_p0.3_mac` | `frontier_p0.3_ibac`, `frontier_p0.3_mac` |

Steps 1 give the primary contrast; steps 1 and 2 give RQ1 whole (including Page's trend); steps 3 to 5 build RQ2, with the middle failure rate last.

**Rule for the pre-registration:** a registered cell not finished by the deadline is reported as "not run", never dropped silently, and any analysis that needs it says so. Cells are resumable, so a batch can be stopped and restarted. Stopping from the end of an order is the planned way to cut; it needs no change to the registered design.

### Time, from the pilot and the frontier test

| | Runs | Llama lane | Frontier lane |
|---|---|---|---|
| Full grid (registered) | 2,700 | 9.3 h (none 2.7, MAC 3.3, IBAC 3.3) | about 0.7 h of model time at 1.9 s per run; the quota decides the real elapsed time (unknown, D09) |

The calendar time is the longer of the two lanes, not their sum.

## Mitigation (decided later; pre-declared so that cutting stays defensible)

Cut from the end of each lane, in this order of preference, and state in the report what each question can then say:

1. **Plan A: no frontier mediator cells** (drop frontier steps 3 to 5): 1,800 runs; Llama 9.3 h. RQ2 is then tested on Llama only, which needs a one-line scope note ("tested on Llama; IBAC's classifier is Llama"); check the proposal's RQ2 sentence for this.
2. **A1: also drop the p = 0.3 IBAC and MAC cells for Llama:** 1,500 runs; Llama 7.2 h. RQ2 compares the arms at two failure regimes instead of three.
3. **A2: also drop `frontier_p0.3_none`:** 1,350 runs. The primary contrast is unaffected; the frontier arm loses its middle point.
4. Beyond that, the floor options: the six no-mediator cells (RQ2 dropped), or the four primary cells (Page's trend and RQ2 dropped).

Not recommended: fewer than 3 seeds (D30), fewer scenarios, or a lower step cap (D07). Two Llama cells at once on one machine is untested and can change a local model's output slightly even with fixed seeds, so it needs a small trial and one mode used throughout.

## Pending / follow-up

Get your supervisor's agreement in writing. Check the proposal's RQ2 sentence (matters only if mitigation 1 is used). Write the registered cells, the two lanes and the not-run rule into the pre-registration (#29), before the freeze (#30). Frontier runs also wait on the quota (D09) and the model choice (D28); `make run-plan` (a single command per lane in this order, with the integrity check after each cell) is a possible helper.
