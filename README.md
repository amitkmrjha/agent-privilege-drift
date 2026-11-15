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

**Phase 0: project setup** (gate G0). Progress is tracked on the [project board](https://github.com/users/amitkmrjha/projects/3).

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
```

Container route (reproducible environment):

```bash
make docker-build && docker compose run --rm harness
make docker-test
```

For real runs on a Mac, use the native Ollama install; the optional `ollama` compose profile is for Linux or CI (Docker on macOS has no GPU access). AI-agent guidance for contributors is in [AGENTS.md](AGENTS.md).

`make pilot`, `make run-cell` and `make analyse` are placeholders that exit with an error until the harness is built (Phases 1 to 4). This section will be updated as they land.

## Documentation

- [PRD 1: Research implementation and experiment runs](docs/prd/PRD_1_Research_Implementation.md)
- [PRD 2: Thesis writing](docs/prd/PRD_2_Thesis_Writing.md)
- [Implementation plan](docs/plan/IMPLEMENTATION_PLAN.md)
- [Issue breakdown](docs/plan/ISSUE_BREAKDOWN.md)
- [Sources: benchmarks and baselines](docs/research-reference/sources.md)

## Licence

Code is released under the [MIT Licence](LICENSE). Third-party benchmarks keep their own licences; see the sources document.
