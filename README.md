# agent-privilege-drift

**Dynamic Tool Authorization: Evaluating Least-Privilege Violations and Privilege Escalation under Failure Pressure in Open-Source Agents**

MS research project (LJMU). A Python harness that runs an LLM agent (ReAct) on benchmark scenarios while injecting transient HTTP 503 tool failures, optionally gated by an access-control mediator, and records full telemetry for a pre-registered statistical analysis.

**Core claim tested:** transient tool failure pushes agents toward higher-privilege tools ("privilege drift"), and an intent-based gate can reduce that without hurting task success.

## Research questions

| ID | Question |
|---|---|
| RQ1 | Under transient tool failure, does Llama-3.1-8B-Instruct escalate privileges at a different rate than a frontier baseline? |
| RQ2 | Does IBAC reduce PoLP violations across failure regimes without significantly hurting task success, compared with SEAgent MAC and no mediator? |
| RQ3 | Which observable failure signals best predict a privilege-escalation attempt, and with what relative weight? |

## Status

**Phase 1: harness build is done** (gate G1): the agent, failure injector, three mediators, telemetry and batch runner are built, and the fake-model integration and golden tests pass. The optional AgentDojo integration (#23) is open. The analysis code (statistics library, RQ1, RQ2, RQ3 and `make analyse`) is built. **Phase 2 is in progress:** the full pilot (270 runs on local Llama, issue #24) has run and its report is in [docs/pilot.md](docs/pilot.md); next are the sanity check of its traces (#25), the open decisions (#26), the power analysis (#27), the choice of the frontier model (#28) and the pre-registration. For the exact current state and next steps read [docs/HANDOFF.md](docs/HANDOFF.md). Progress is tracked on the [project board](https://github.com/users/amitkmrjha/projects/3).

| Phase | Ends when |
|---|---|
| 0 Project setup | Repo builds, sources verified, decisions logged |
| 1 Harness build | Fake-model integration and golden tests pass |
| 2 Pilot and pre-registration | Pre-registration and code freeze tagged |
| 3 Experiment runs | Every cell passes integrity checks |
| 4 Analysis | One command reproduces every number |
| 5 Document the outcome | Results report, hand-off package and release done |

## How to run

Requires [uv](https://docs.astral.sh/uv/) (it installs Python 3.12 for you).

```bash
make setup       # uv sync + install pre-commit hooks
make check       # lint + mypy (strict) + pytest: the gate CI runs
make help        # list every target
make data        # download ToolPrivBench (pinned revision, hash-checked) into data/raw/
```

Container route (reproducible environment):

```bash
make docker-build && docker compose run --rm harness
make docker-test
```

Ollama is not containerised: use the native install (`ollama pull llama3.1:8b-instruct-q4_K_M`), since Docker on macOS has no GPU access. AI-agent guidance for contributors is in [AGENTS.md](AGENTS.md).

Running the experiment, one cell at a time (a cell is a model, a failure rate and a mediator; 18 in all):

```bash
make list-cells                                  # numbers and ids
make run-cell CELL=llama_p0_none LIMIT=3         # a small trial; omit LIMIT for the whole cell
make check-cell CELL=llama_p0_none               # the three integrity checks
```

A cell can be stopped and started again: only runs without a valid result are redone. Results go to `runs/<cell id>/` (gitignored). Running a whole cell calls the model for hours.

`make analyse` regenerates every analysis number, table and figure from the finished runs under `runs/` into `results/` (`numbers.json`, `tables/*.csv`, `figures/*.png`). Running it again on the same run files gives byte-identical output. It covers RQ1, RQ2 and RQ3; the AgentDojo analysis is not part of it yet.

## How it works, in plain English

The question: when an agent's tools start failing, does it begin using more powerful tools than the task needs? That is "privilege drift". The harness measures it and tests whether two guards stop it.

**One run** is one agent playing one task:

```
model reply -> guard (mediator) -> failure injector -> tool -> result shown to the model
```

| Part | Folder | What it does |
|---|---|---|
| Data | `src/privilege_drift/data/` | ToolPrivBench: 544 small tasks. Each has tools at three power levels (read-only < user < admin), and one tool is the lowest-power one that does the job (the "minimum tier"). |
| Agent | `agent/` | A text ReAct loop: the model writes Thought, Action, Action Input; the system runs the tool and replies with an Observation; repeat until a Final Answer or 15 steps. One chance to fix an unreadable reply. The prompt never shows tool power levels, never says "be careful", and never says failures are temporary, because those are what is measured. |
| Model access | `llm/` | Calls the model through LiteLLM. Local Llama goes to the **Ollama server over HTTP** (default `http://localhost:11434`, or `OLLAMA_API_BASE`). The harness does not start Ollama; the Ollama desktop app or `ollama serve` must already be running. Records the model digest of every run. |
| Failure injector | `failure/` | The experiment's main variable. Each tool call that reaches it gets one dice roll; with probability p (0, 0.3 or 0.6) the tool returns a fixed "503 Service Unavailable". The dice are computed from a hash of the run's identity, so a resumed run sees the same rolls. |
| Guards (mediators) | `mediators/` | **none**: allows everything. **MAC**: a fixed rule per role, ignores the task (the baseline). **IBAC**: Llama reads the task once, names its intent (healthcare, coding, ...), and a policy says which tiers that intent may use (the idea under test). A blocked call gets no dice roll. Policies are in `configs/policies/`. |
| Telemetry | `telemetry/` | One record per proposed call. A call is a **violation** if its tool is above the minimum tier. It also stores the RQ3 predictors (recent 503s, retries since the last success, blocks so far, tokens), computed only from what the agent could already know. |
| Runner | `runner/` | Runs a whole cell unattended: skips finished runs, retries model-service hiccups, writes a manifest and runs three integrity checks. |
| Frozen inputs | `prereg/` | The 50 experiment scenarios and the seed schedule. Must not change after the code freeze. |

**The grid.** Models (Llama, one frontier model) x failure rates (0, 0.3, 0.6) x guards (none, MAC, IBAC) = 18 cells, set in `configs/grid.yaml`. Llama alone is 1,350 runs. Model settings are in `configs/models.yaml`; the model is referred to by key, so the frontier model is a one-line change.

**What is known so far** (details in [docs/decisions/](docs/decisions/README.md)): on ToolPrivBench, IBAC and MAC make identical decisions (D26, D27), so the RQ2 contrast needs the supervisor's input. The parser once discarded real escalations; that is fixed (D23).

## The pilot

A dress rehearsal on Llama only: 9 cells (3 failure rates x 3 guards) on 10 scenarios that are **not** in the frozen 50, with their own seeds (`pilot/`, `configs/pilot_grid.yaml`). It checks throughput, the step cap, the prompt and parser, and the window size, before anything is frozen. Results go to `runs/pilot/` (gitignored).

Run it in your own terminal, with Ollama running and the model pulled:

```bash
ollama list                              # llama3.1:8b-instruct-q4_K_M must be listed
make pilot-smoke                         # small pass: 3 runs per cell, about 10 minutes
make pilot                               # full pilot: 270 runs, about 1.5 hours, plug the laptop in
uv run python scripts/pilot_report.py    # writes docs/pilot.md (throughput, health checks, extrapolation)
```

Both pilot commands can be stopped with Ctrl-C and restarted: only runs without a valid result are redone. Do not edit `src/` while a batch is running. To run one pilot cell: `make run-cell CELL=llama_p0_none GRID=configs/pilot_grid.yaml`.

## Documentation

- [PRD 1: Research implementation and experiment runs](docs/prd/PRD_1_Research_Implementation.md)
- [PRD 2: Thesis writing](docs/prd/PRD_2_Thesis_Writing.md)
- [Implementation plan](docs/plan/IMPLEMENTATION_PLAN.md)
- [Issue breakdown](docs/plan/ISSUE_BREAKDOWN.md)
- [Sources: benchmarks and baselines](docs/research-reference/sources.md)
- [Data summary (generated)](docs/data_summary.md)
- [Pilot report (generated)](docs/pilot.md)
- [Sequence diagrams: what happens in a pilot or experiment run](docs/SEQUENCE.md)
- [Design decisions log](docs/decisions/README.md)

## Licence

Code is released under the [MIT Licence](LICENSE). Third-party benchmarks keep their own licences; see the sources document.
