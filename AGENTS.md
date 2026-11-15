# AGENTS.md

Guidance for AI coding agents (Claude Code, Copilot, Cursor, Codex, ...) working in
**agent-privilege-drift**. `CLAUDE.md` points here; this file is the single source of truth.

## What this repo is

A Python research harness for an MS thesis. It runs an LLM agent (ReAct) on benchmark
scenarios while injecting transient HTTP 503 tool failures, optionally gated by an
access-control mediator (none, SEAgent-style MAC, intent-based IBAC), records full
telemetry, and feeds a scripted, pre-registered statistical analysis.

Research questions: RQ1 (Llama vs frontier escalation under failure), RQ2 (IBAC vs MAC vs
none), RQ3 (which failure signals predict escalation). Details: `docs/prd/`,
`docs/plan/IMPLEMENTATION_PLAN.md`, `docs/plan/ISSUE_BREAKDOWN.md`.
Source availability and licences: `docs/research-reference/sources.md`.

Package: `src/privilege_drift/` (import `privilege_drift`, CLI `privilege-drift`).

## Setup and everyday commands

Requires [uv](https://docs.astral.sh/uv/). Python 3.12 is installed by uv.

```bash
make setup          # uv sync + pre-commit hooks
make check          # ruff + mypy (strict) + pytest   <- run before every PR
make help           # list every target
```

Individual gates: `make format`, `make lint`, `make test`. Container route:
`make docker-build`, `make docker-test`, `docker compose run --rm harness`.
`pilot`, `run-cell` and `analyse` are placeholders until the later phases land.

## Rules of the road

1. **Never invent results.** Every reported number must be reproducible from run data by a
   script. Do not hand-write figures, p-values or "expected" outcomes into docs or code.
2. **No secrets.** Never commit `.env`, API keys or tokens. Keys come from env vars;
   `.env.example` lists the names only.
3. **Respect the freeze.** Once the pre-registration is tagged (issue "Tag and hash the
   pre-registration and code freeze"), do not change `prereg/`, the frozen subsets, the seed
   schedule, `configs/grid.yaml` or anything that alters experiment behaviour. Record any
   unavoidable change in the deviations log instead.
4. **Seeds and sampling are explicit.** Pass a seed on every run. Keep the sampling constants
   (temperature, top-p, max tokens) identical across arms. Set Ollama `num_ctx` explicitly;
   its default silently truncates long histories.
5. **Do not spend money or hours unasked.** No paid frontier-model calls, full batches or
   overnight runs without the user's explicit go-ahead. Tests use a fake model or the
   response cache, never a live API.
6. **Generated data stays out of git.** `runs/` and `data/raw/` are gitignored. Do not commit
   them or add them to Docker images.
7. **Licences matter.** ToolPrivBench data is CC-BY-4.0 (attribute it). Its code has no
   LICENSE file: do not copy it; re-implement from the paper. See `sources.md`.
8. **Type everything.** New code is fully annotated and `mypy --strict` clean. Unit tests
   accompany code.
9. **Keep `Makefile` and `.github/workflows/ci.yml` in step.** CI runs `make check`.
10. **Log decisions.** Design decisions and deviations go in `docs/decisions/` and the
    deviations log, not only in commit messages.

## Agent boundaries (do NOT do)

- No `git push --force`, no force-push to `main`, no pushing directly to `main`.
- No merging a PR or cutting a release or tag unless the user asks you to in that turn.
- No `docker push` or publishing anywhere.
- No emailing or contacting third parties (for example paper authors) on the user's behalf.
- No editing issue text on the GitHub board without asking.
- Do not copy content from private or employer repositories into this public repo.

## Workflow

- One issue, one branch `feat/<issue-number>-<short-name>` (or `chore/`, `docs/`), one PR
  whose body contains `Closes #<n>`. Squash-merge. Plain titles, no ID codes.
- Pick the next issue by priority, then phase; respect "Blocked by" links.
- Definition of done: acceptance test passes, `make check` green, docs updated, any design
  change or deviation logged.
- Add a `Co-Authored-By` trailer to commits made with an AI assistant.
