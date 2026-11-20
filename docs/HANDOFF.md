# Hand-off: where the project is and how to resume

Last updated 2026-11-19. Read this first in a new session, then `AGENTS.md`.

## In one paragraph

The research harness for the thesis is **built and tested** (Phase 1 done except the optional AgentDojo
issue #23). It has run only small slices on the real local model so far. The next step is the
**pilot** (#24), then the pre-registration and code freeze, then the experiment runs. The deadline in
the PRD is **2026-12-02**; whether that means the experiments or the whole thesis is not confirmed.

- Repo: https://github.com/amitkmrjha/agent-privilege-drift (`main` is the truth; work by branch and PR)
- Board: https://github.com/users/amitkmrjha/projects/3 (17 of 44 issues Done)
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
| Decisions | `docs/decisions/` | D01 to D27, read the README index |
| Tests | `tests/` | about 350, including a golden test; `make check` runs everything CI runs |

## What has been learned (details in the decision records)

1. **IBAC and MAC make identical decisions on ToolPrivBench** (D27), and **MAC is a perfect baseline**
   because it uses the benchmark's own risk labels (D26). So the RQ2 contrast "IBAC vs MAC" is empty
   by construction here. RQ1 and RQ3 are unaffected.
2. The IBAC classifier recovers the domain on 42 of 50 frozen scenarios (84 %), with no unreadable
   replies (D27).
3. Real Llama escalates after repeated 503s in the few runs seen (an anecdote, not a result).
4. The first real runs showed Llama invents `### User:` turns after an action; a reply holding a
   real escalation was being discarded. **Fixed** in the parser (D23, "Update").

## Decisions waiting for the author or the supervisor

- **RQ2 framing** (D26, D27): accept that IBAC equals MAC on ToolPrivBench and rest the IBAC claim on
  AgentDojo (#23), or reframe RQ2. Needs the supervisor, because the submitted proposal states RQ2.
- **Is 2026-12-02 the experiments or the whole thesis?** Not confirmed.
- **Frontier arm scope:** the plan runs the frontier model in all 9 cells (1,350 runs). Running it only
  on the "no mediator" cells (450 runs) and running MAC/IBAC on Llama only would save about 900
  frontier runs. This is not one of the plan's reduction levers; the supervisor should agree.
- 9 decisions are still **Proposed** (D05, D18, D19, D21, D22, D23, D25, D26, D27) and 2 wait for the
  pilot (D09 API budget, D14 window size k). All are settled in issue #26 before the pre-registration.

## The pilot (#24)

- A **small pass** (3 runs per cell, 27 runs, about 10 minutes): `make pilot-smoke`.
- The **full pilot** (270 runs, about 1.5 hours, plug in the laptop): `make pilot`. Both are
  resumable; they only run what has no valid result yet. Results go to `runs/pilot/` (gitignored).
- Then `uv run python scripts/pilot_report.py` writes `docs/pilot.md` (throughput, the 5 % health
  checks, extrapolation to the full grid). Commit that and finish #24.
- Requires Ollama running with `llama3.1:8b-instruct-q4_K_M` (`ollama list`).
- Pilot results from before the parser fix are in `runs/pilot_before_parser_fix/` (not committed).

## Frontier model: first small test (2026-11-20)

- `configs/pilot_frontier_grid.yaml` runs the frontier model only, no mediator, on the 10 pilot scenarios
  (results in `runs/pilot_frontier/`, gitignored). Needs `GEMINI_API_KEY` in the shell:
  `set -a; source .env; set +a`, then `uv run privilege-drift run-cell frontier_p0_none --limit 3 --grid configs/pilot_frontier_grid.yaml`.
  `.env` is not loaded automatically by `uv run` or `make`.
- The model is now `gemini/gemini-3.5-flash-lite` (provisional, D28). `gemini-2.5-flash` was closed to new
  users; `gemini-3.8-flash` was overloaded and rejects `temperature` and `top_p` (see `omit_params`, D28).
- Result: 9 runs finished with no parse errors and no escalation, but that is one easy scenario.
  **Open: 429 quota errors.** One run was rate-limited three times before succeeding, so the retry
  waits are too short and the account's quota is unknown (D09). Revisit before the frontier batch.

## Next steps, in order

1. Finish the pilot (small pass reviewed, then `make pilot`), write `docs/pilot.md`, close #24.
2. Get a **Gemini API key** (put it in `.env` as `GEMINI_API_KEY`, which is gitignored; never paste it
   into a chat). Run a **small frontier slice (about 50 calls)** to measure real rate limits and cost.
   That decides whether the full frontier arm fits (D09, D20, issue #28). This also finishes #12.
3. Talk to the supervisor (RQ2 framing, frontier scope, what 2 December means).
4. Phase 2: sanity-check the pilot (#25), settle the open decisions (#26), power analysis (#27),
   choose the frontier model (#28), write the pre-registration (#29), tag and hash the freeze (#30).
5. Phase 3: run the Llama grid (1,350 runs, about 8 to 10 hours of machine time) and the frontier
   arm, clean the data (#33). Use `make run-cell CELL=<id>` and `make check-cell CELL=<id>`.
6. Phases 4 and 5: statistics, the three analyses, one-command reproduction, results report, release.

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
