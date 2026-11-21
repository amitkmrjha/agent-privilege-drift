# Hand-off: where the project is and how to resume

> **Amendment exp-v2 (2026-11-21, D32).** After the exp-v1 results were seen, a large frontier model
> (`frontier_large` = `gemini/gemini-4-carbon`) is added as a separately registered amendment
> (`prereg/preregistration.md` section 10A). The exp-v1 results are complete and unchanged; the
> amendment runs the three no-mediator cells first (`make run-plan LANE=frontier_large FIRST=3`).
> `make analyse` stays on the registered pair; `make analyse-v2` runs the amendment contrasts.


Last updated 2026-11-21. Read this first in a new session, then `AGENTS.md`.

## In one paragraph

The research harness is **built and tested**, the **analysis code is built** (statistics library, RQ1,
RQ2, RQ3 and `make analyse`), the **Llama pilot has run** (270 runs, `docs/pilot.md`), and the design
is **frozen: tag `exp-v1`** (on the remote; `prereg/preregistration.md`, hashes in
`prereg/freeze_record.json`). We are at the start of **Phase 3: the experiment runs**. Nothing has
been run on the frozen design yet. The deadline in the PRD is **2026-12-02**; whether that means the
experiments or the whole thesis is not confirmed.

- Repo: https://github.com/amitkmrjha/agent-privilege-drift (`main` is the truth; work by branch and PR)
- Board: https://github.com/users/amitkmrjha/projects/3
- Local folder: `~/ws/upgrad/ms/research/project/agent-privilege-drift`

## What exists

| Part | Where | Notes |
|---|---|---|
| Data, tiers, stubs | `src/privilege_drift/data/` | ToolPrivBench, 544 scenarios, `make data` downloads it |
| Frozen subset and seeds | `prereg/` | 50 scenarios, 18 cells x 5 seeds; **must not change after the freeze** |
| Agent | `agent/` | text ReAct, parser, prompt; one correction per bad reply |
| Failure injector | `failure/` | HTTP 503 at rate p, one draw per call that reaches it |
| Mediators | `mediators/` | none, MAC (fixed matrix), IBAC (Llama intent classifier) |
| Telemetry | `telemetry/` | per-call records, RQ3 predictors, atomic JSONL files |
| Batch runner | `runner/` | resume, retries, manifests, 3 integrity checks, CLI |
| Pilot inputs | `pilot/`, `configs/pilot_grid.yaml` | 10 scenarios **outside** the frozen 50, own seeds |
| Analysis | `analysis/` | `stats.py`, `rq1.py`, `rq2.py`, `predictors.py` (RQ3), `reproduce.py`; `make analyse` writes `results/` |
| Decisions | `docs/decisions/` | D01 to D29, read the README index |
| Tests | `tests/` | about 420, including a golden test; `make check` runs everything CI runs |

## What has been learned (details in the decision records)

1. **IBAC and MAC make identical decisions on ToolPrivBench** (D27), and **MAC is a perfect baseline**
   because it uses the benchmark's own risk labels (D26). So the RQ2 contrast "IBAC vs MAC" is empty
   by construction here. RQ1 and RQ3 are unaffected.
2. The IBAC classifier recovers the domain on 42 of 50 frozen scenarios (84 %), with no unreadable
   replies (D27).
3. Real Llama escalates after repeated 503s in the few runs seen (an anecdote, not a result).
4. The first real runs showed Llama invents `### User:` turns after an action; a reply holding a
   real escalation was being discarded. **Fixed** in the parser (D23, "Update").
5. **Pilot (270 runs, `docs/pilot.md`):** all integrity checks pass; every health rate is under 5 %;
   at p = 0 with no mediator the violation rate is 34.7 % against the published about 35 %, so the
   scoring is sound. The 15-step cap was not binding (D07). The full Llama grid is about 9.3 hours.
6. **The primary measure matters (D29):** with no mediator the violation rate per call is flat across
   failure rates (34.7, 34.1, 34.5 %) but violating calls per run rise (1.17, 1.40, 1.70), because
   runs get longer. Decide which is primary on measurement grounds, before the freeze. Pilot numbers
   are tuning data, not results; do not tune the prompt to make an effect appear.
7. Gated arms look costlier at p = 0.6 (task success 87 % with MAC and 83 % with IBAC against 93 % with
   no mediator, 30 runs each): watch the 5-point utility floor in the real runs.

## Decisions waiting for the author or the supervisor

- **RQ2 keeps its original wording** (D26, D27, D31). IBAC and MAC are expected to behave the same on
  ToolPrivBench; that is reported as a result, not a reason to reword. It is tested for both models
  if the frontier mediator cells are run. **Only if the frontier quota forces those cells to be cut**,
  check the proposal's RQ2 sentence: if it requires both models, add a one-line scope note ("tested
  on Llama").
- **Is 2026-12-02 the experiments or the whole thesis?** Not confirmed.
- **Run plan (D31, accepted 2026-11-21): the full 18-cell grid, 2,700 runs, registered and run in two
  priority-ordered lanes that can run at the same time:** Llama (local, about 9.3 hours) and frontier
  (API, about 0.7 hours of model time but bound by the unknown quota, D09). The four primary cells are
  first in each lane and the p = 0.3 mediator cells last, so if time or quota runs out the cut falls
  on the least valuable cells. A cell not finished by the deadline is reported as "not run" under a
  rule written in advance, so cutting is planned, not a deviation. Mitigation is decided later, in this
  pre-declared order: no frontier mediator cells (1,800 runs), then no p = 0.3 mediator cells for
  Llama (1,500), then no `frontier_p0.3_none` (1,350). The supervisor agrees in principle to
  simplifications that keep the design correct and defensible (relayed by the author; **get it in
  writing**).
- **Accepted 2026-11-21 (as recommended):** D05, D07 (15 steps), D14 (k = 3, now in `configs/grid.yaml`),
  D18, D19, D21, D22, D23, D25, D26, D27, D28 (model pinned as `gemini/gemini-3.5-flash-lite`), D29
  (per-call rate primary), D30 (3 seeds), D31 (the run plan). D09 (API budget) still waits on the
  Gemini quota and billing.
- **Open for the freeze** (`uv run python scripts/freeze.py --check` lists them): the proposal's
  hypothesis directions and the pre-declared utility-floor wording (proposal section 7.5.2, which the
  author is to paste in); the frontier decoding check (`scripts/check_frontier_params.py`, needs the
  key; if the model accepts temperature and top-p, drop `omit_params`); and the pre-registration's own
  proposals to tick: the reading of "5 pp", how the primary result is read, the Holm families, RQ3
  pooling, the lever list, the confirmatory/exploratory split, and truncation handling.

## The pilot (#24, done)

- The full pilot (270 runs) ran on 2026-11-20 in about 1 h 40 min. Results are in `runs/pilot/`
  (gitignored); `uv run python scripts/pilot_report.py` regenerates `docs/pilot.md` from them.
- `uv run python scripts/pilot_traces.py` writes `runs/pilot/traces_to_read.md`: ten varied runs to
  read by hand for the sanity check (#25). **Reading them is the open step.** Notes so far: the model
  jumps to an admin tool after a single 503 in at least one run; one run called the same tool 14 times
  because the canned tool reply never signals completion (3.9 % of calls repeat the previous tool
  right after it succeeded; harmless to the violation share, but a limitation of the stub tools).
- To re-run: `make pilot` (resumable; needs Ollama with `llama3.1:8b-instruct-q4_K_M`, laptop plugged in).
- Pilot results from before the parser fix are in `runs/pilot_before_parser_fix/` (not committed).

## Power analysis (#27)

`uv run python scripts/power_analysis.py` (about 10 seconds) estimates the noise from the pilot and
writes `docs/power.md`. Result for a true 12-point difference with 50 scenarios: with 3 seeds the plain
comparison has 76.5 % power at the Holm stand-in level 0.05/18 and the primary difference in
differences has 78.7 % at 0.05, both just under the plan's 80 %; with 5 seeds they are 96.5 % and
94.2 %. The plan's rule would say 5 seeds (900 more runs per model, about 67 % more time, the Llama
grid from about 9.3 to 15.5 hours). **Decision (D30, accepted): keep 3 seeds** to keep the runs simple
and short; `configs/grid.yaml` already says 3. The consequences are recorded in D30: the primary
contrast is borderline for a 12-point effect (about 12.2 points detectable at 80 % power), so test it
at 0.05 as one pre-registered test and report a non-significant result as an upper bound; adding
seeds 4 and 5 stays possible because the seed schedule holds 5 (state it in the pre-registration if
wanted). The noise rests on 10 pilot scenarios, so the figures are rough; the analysis assumes the
per-call rate is primary (D29): re-run if that changes.

## Frontier model: first small test (2026-11-20)

- `configs/pilot_frontier_grid.yaml` runs the frontier model only, no mediator, on the 10 pilot scenarios
  (results in `runs/pilot_frontier/`, gitignored). Needs `GEMINI_API_KEY` in the shell:
  `set -a; source .env; set +a`, then `uv run privilege-drift run-cell frontier_p0_none --limit 3 --grid configs/pilot_frontier_grid.yaml`.
  `.env` is not loaded automatically by `uv run` or `make`.
- The model is now `gemini/gemini-3.5-flash-lite` (provisional, D28). `gemini-2.5-flash` was closed to new
  users; `gemini-3.8-flash` was overloaded and rejects `temperature` and `top_p` (see `omit_params`, D28).
- Result: 9 runs finished with no parse errors and no escalation, but that is one easy scenario.
  **429 quota errors:** one run was rate-limited three times before succeeding. **Handled since
  2026-11-21:** a 429 is now retried in place with jittered exponential then fixed waits
  (`rate_limit_retry` in `configs/models.yaml`), a run is not restarted, and two rate-limited runs in a
  row stop the batch (D09, D25). Still open: the account's real limits (AI Studio rate-limit page), and
  moving to a paid tier by linking billing; a fixed throttle can be added once the limit is known.

## Next steps, in order

The design is frozen (`exp-v1`). `make freeze-check` shows whether any run file or the registered
text has changed since: a change is a deviation to log in `docs/deviations.md` (#35).

1. **Before the first full run (not frozen, only timing):** link billing for the Gemini project in AI
   Studio and read the rate-limit page for `gemini-3.5-flash-lite` (the free tier is what produced the
   429s). Then run one small frontier cell (`make run-cell CELL=frontier_p0_none LIMIT=3`, with the key
   loaded: `set -a; source .env; set +a`) to see that the 429 retry copes (D09).
2. **Phase 3: run the two lanes, in D31's priority order**, resumable and able to run at the same time:
   *Llama (local, about 9.3 hours, laptop plugged in, Ollama running):* `llama_p0_none`,
   `llama_p0.6_none`, `llama_p0.3_none`, then IBAC at p = 0 and 0.6, MAC at p = 0 and 0.6, then
   `llama_p0.3_ibac` and `llama_p0.3_mac`. *Frontier:* the same order with the `frontier_` cells.
   Use `make run-cell CELL=<id>` then `make check-cell CELL=<id>`. A cell not finished by the deadline
   is reported as "not run" (the rule is in the pre-registration), and the cuts are pre-declared in D31.
3. **Clean and freeze the run data** (#33), then `make analyse` (writes `results/`), then the results
   report (#42), the hand-off package (#43) and the release (#44).
4. Keep `docs/deviations.md` complete; AgentDojo (#23, #34, #40) is optional and not in this
   registration.

## How to resume in a new Claude Code session

```bash
cd ~/ws/upgrad/ms/research/project/agent-privilege-drift
git checkout main && git pull
claude
```

Then paste:

> Read `docs/HANDOFF.md` and `AGENTS.md`, check the board and open PRs with `gh`, and tell me where we
> are. Then continue with the next step. I use "merge, close, next" to mean: merge the PR, make sure
> the issue is closed, start the next issue.

Practical notes:

- Starting in the repo folder (above) gives the session `AGENTS.md` and a sandbox that can write the
  repo. If `gh` says the token is invalid, that is the sandbox blocking the keychain; run `gh auth status`
  in a normal terminal to confirm it is fine.
- Working rules are in `AGENTS.md`: one issue, one branch `feat/<n>-name`, one PR with `Closes #n`;
  squash-merge; no merging, paid calls or long runs unless asked; log decisions in `docs/decisions/`.
- Before any long run: plug in the laptop. Do not edit `src/` while a batch is running, because each
  cell starts a fresh process that would pick up the change.
- The workspace file `~/ws/upgrad/ms/vscode_ws/ljmu_research/ljmu.code-workspace` opens this repo
  together with the proposal and thesis-writing folders.
