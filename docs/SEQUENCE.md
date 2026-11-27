# Sequence diagrams: what happens when the pilot or the experiment runs

These diagrams are Mermaid. GitHub draws them in the browser; in VS Code use a Mermaid preview extension.
The pilot and the real experiment use the same code. Only the grid file, the scenarios, the seeds and the
model differ (see the table at the end).

## 1. The whole chain: `make pilot` (or `make run-cell`) to result files

```mermaid
sequenceDiagram
    autonumber
    actor You
    participant Make as Makefile
    participant CLI as cli.py
    participant Grid as runner/grid + inputs
    participant Batch as runner/batch.py
    participant Item as runner/execute.py
    participant Disk as runs/ folder
    participant Check as runner/integrity.py

    You->>Make: make pilot
    Make->>CLI: list-cells (pilot grid)
    CLI-->>Make: 9 cell ids

    loop for each of the 9 cells
        Make->>CLI: run-cell CELL (pilot grid)
        CLI->>Grid: load grid, subset, seed schedule, data
        Grid-->>CLI: scenarios + seeds (data hash checked)
        CLI->>Grid: plan_cell
        Grid-->>CLI: 30 work items (10 scenarios x 3 seeds)
        CLI->>Batch: run_cell(items, deps)

        loop for each work item
            Batch->>Disk: is a valid result file already there?
            alt already finished
                Disk-->>Batch: yes, skip
            else not finished
                Batch->>Item: run_item (with retries)
                Note over Item: one run, see diagram 2
                Item-->>Batch: RunTelemetry
                Batch->>Disk: write raw file, then main file (atomic)
            end
        end

        Batch->>Disk: write manifest.json
        Batch-->>CLI: CellReport
        Make->>CLI: check-cell CELL
        CLI->>Check: check_cell
        Check->>Disk: read all runs
        Check-->>CLI: 3 checks: runs present, injection replay, tier attribution
        CLI-->>Make: exit 0 or 1 (1 stops the whole pilot)
    end

    You->>You: uv run python scripts/pilot_report.py
    Note over You,Disk: reads runs/pilot, writes docs/pilot.md
```

## 2. One run: agent, guard, failure injector, tool, model

```mermaid
sequenceDiagram
    autonumber
    participant Item as run_item
    participant Agent as ReActAgent
    participant LLM as LLMClient
    participant Ollama as Ollama server (or Gemini)
    participant Parser as parser.py
    participant Guard as Mediator (none / MAC / IBAC)
    participant Inj as FailureInjector
    participant Tool as StubExecutor
    participant Rec as TelemetryRecorder

    Item->>Guard: build mediator for the cell
    Item->>Inj: build injector (p, dice key)
    Item->>Agent: run(scenario, seed)
    Agent->>Guard: start_run(scenario)

    opt mediator is IBAC
        Guard->>LLM: classify the task (always Llama, seed 0)
        LLM->>Ollama: HTTP POST /api/chat
        Ollama-->>LLM: {"intent": "healthcare", "confidence": 0.9}
        LLM-->>Guard: intent (one retry if unreadable, else classifier_failed)
    end

    loop each step, up to max_steps (15)
        Agent->>LLM: complete(messages, seed, stop = "Observation:")
        LLM->>Ollama: HTTP POST (num_ctx 8192, temp 0.2)
        Ollama-->>LLM: reply text, token counts
        LLM-->>Agent: LLMResult
        Agent->>Parser: parse_step(reply)

        alt unreadable reply
            Parser-->>Agent: ParseFailure
            Agent->>Rec: record parse_error
            Agent->>LLM: one correction re-prompt
            Note over Agent: a second failure ends the run (format_error)
        else Final Answer
            Parser-->>Agent: ParsedFinal
            Agent->>Rec: record final answer
            Note over Agent: run ends (final_answer)
        else Action
            Parser-->>Agent: ParsedAction (tool, arguments)
            Agent->>Guard: gate(call)
            alt guard blocks
                Guard-->>Agent: Decision(allow = false)
                Note over Agent,Inj: injector is skipped, so no dice roll
                Agent->>Agent: result = 403 Access denied (fixed text)
            else guard allows
                Guard-->>Agent: Decision(allow = true)
                Agent->>Inj: injector(call, execute)
                Inj->>Inj: draw = SHA-256(seed, cell, scenario, seed idx, n)
                alt draw < p
                    Inj-->>Agent: 503 Service Unavailable (tool not run)
                else draw >= p
                    Inj->>Tool: execute(call)
                    Tool-->>Inj: 200 canned output
                    Inj-->>Agent: result
                end
            end
            Agent->>Rec: StepRecord (proposed call, decision, result)
            Note over Rec: logs violation BEFORE the guard, plus RQ3 predictors from earlier calls only
            Agent->>Agent: append "Observation: result" to the history
        end
    end

    Note over Agent: loop ended without Final Answer means max_steps
    Agent-->>Item: RunTrace
    Item->>Rec: finish(trace)
    Rec-->>Item: RunTelemetry (records + run summary)
```

## 3. Failures that are not agent behaviour (infrastructure retries)

```mermaid
sequenceDiagram
    autonumber
    participant Batch as runner/batch.py
    participant Item as run_item
    participant LLM as LLMClient
    participant Ollama as Ollama server
    participant Log as infrastructure_errors.jsonl
    participant Disk as runs/ folder

    Batch->>Item: run_item (attempt 1)
    Item->>LLM: complete(...)
    LLM->>Ollama: HTTP POST
    Ollama--xLLM: timeout or connection error
    LLM-->>Item: raises LLMCallError
    Item-->>Batch: error bubbles up
    Batch->>Log: append the error (not run data)
    Note over Batch: wait 2 s, then 4 s, then 8 s (max 4 attempts)
    Batch->>Item: run_item again from the start
    alt succeeds
        Item-->>Batch: RunTelemetry
        Batch->>Disk: write result files
    else still failing after 4 attempts
        Batch->>Disk: write no result file
        Note over Batch,Disk: run is listed as unfinished in manifest.json and redone on the next invocation
    end
```

A missing API key (`MissingCredentialError`) is different: it stops the whole batch instead of being retried.

## 4. Pilot compared with the actual experiment

| | Pilot | Actual experiment |
|---|---|---|
| Command | `make pilot` | `make run-cell CELL=<id>` then `make check-cell CELL=<id>`, per cell |
| Grid file | `configs/pilot_grid.yaml` | `configs/grid.yaml` |
| Models | Llama only | Llama, then the frontier model |
| Scenarios | 10, outside the frozen 50 (`pilot/subset_10.json`) | the frozen 50 (`prereg/subsets/`) |
| Seeds | `pilot/seed_schedule.json` | `prereg/seed_schedule.json` |
| Runs | 9 cells x 30 = 270 | 18 cells x 150 = 2,700 |
| Results | `runs/pilot/` | `runs/<cell id>/` |
| Afterwards | `scripts/pilot_report.py` writes `docs/pilot.md` | cleaning, then the Phase 4 analysis |

For the frontier cells, the model call inside the step loop of diagram 2 goes to the Gemini API instead of Ollama (key from `.env`). IBAC
still classifies with Llama, so Ollama must be running for those cells too.
