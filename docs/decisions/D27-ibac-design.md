# D27: How IBAC is built, and what it can and cannot separate on ToolPrivBench

- **Status:** Proposed (the author confirms; the finding below needs a decision in #26 before pre-registration)
- **Date logged:** 2026-11-19
- **Related:** #20, #23, #26, #38, D13, D18, D26

## Decision

1. **Intents are the 8 ToolPrivBench domains** (`configs/intents.yaml`): business, coding, database, education, government, healthcare, infrastructure, media. This is what the issue and plan specify, and it lets the classifier be scored against each scenario's own domain label. The category descriptions say nothing about permissions.
2. **The classifier reads only the trusted task.** Its prompt holds the category list and `Request: <task>`. It never sees tools, tool results or the agent's words. It is always Llama (PRD I7), with one fixed seed (0), so a task always gets the same answer, and the answer is remembered for the batch so each task is classified once, not once per run.
3. **Unreadable output is a classifier failure (D13):** one retry saying what was wrong, then `failed`. A failed classification applies the most restrictive policy (`fallback`, only `read_only`), which blocks every ToolPrivBench tool, and the telemetry logs `classifier_failed`. Errors from the model service are not classifier failures: they propagate and the batch retries the run.
4. **Policy: `configs/policies/ibac_policy.yaml`** gives each intent a highest allowed tier. A call is allowed when the tool's tier is at or below it. The optional per-tool allow-list in the issue is not built; nothing uses it.
5. **The classification is logged** on every call record and in the run summary (`classifier_intent`, `classifier_conf`, `classifier_failed`). The classifier's own tokens and latency are not in the run telemetry.
6. **The `intent` argument of `gate` is ignored.** IBAC holds the intent it classified in `start_run`.

## Measured: classifier accuracy on the 50 frozen scenarios

Run on 2026-11-19 with `scripts/classifier_accuracy.py`: local Ollama, `llama3.1:8b-instruct-q4_K_M`, seed 0, shared sampling settings, two minutes in all.

| | |
|---|---|
| Scenarios | 50 |
| Correct domain | 42 (84 %) |
| Unreadable (failed) | 0 |
| Wrong | database to business 3; coding to business 1, to infrastructure 1; database to healthcare 1; infrastructure to database 1; media to business 1 |

Zero failures means the model followed the JSON format every time. To be copied into `docs/pilot.md` with the model digest when the pilot runs; re-run the script then.

## Finding: on ToolPrivBench, IBAC and MAC make the same decisions

Under D18 ToolPrivBench has two tiers, and no ToolPrivBench task needs an admin tool (three standard tools always suffice). So the only sensible policy gives every intent the same ceiling, `user`, as the shipped policy does. With one policy for all intents:

- A **correct or wrong** classification changes nothing, because every intent allows the same tiers. The 84 % accuracy has no effect on the violation rate.
- IBAC blocks exactly what MAC blocks (the risk tools) and allows exactly what MAC allows.
- The only differences are the failure fallback (blocks everything, which would hurt task success) and the extra classifier call.

So the IBAC-versus-MAC contrast on ToolPrivBench is empty by construction, not because IBAC does or does not work. A contrast needs tasks whose required privilege differs, which is what AgentDojo's task suites have.

## Measured again in the pilot (2026-11-20)

On the 10 pilot scenarios (not in the frozen 50), IBAC runs classified 9 of 10 tasks into the benchmark's own domain (90 %), with no unreadable replies; the one miss was "look up his email address" (database, classified as business, confidence 1.0), an understandable ambiguity. Model digest `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e`, recorded in every manifest. Both are in `docs/pilot.md`. As this section's finding says, the policy is the same for every intent, so the miss changes nothing.

## Options for #26

1. **Accept and report it.** On ToolPrivBench, IBAC equals MAC; say so plainly, and make the IBAC claim rest on AgentDojo (#23), which then should not be dropped.
2. **Make the policy differ by intent** (for example media may use only `read_only`). That would manufacture a difference from labels I would be inventing, and would hurt task success for those intents. I do not recommend it.
3. **Reframe RQ2** as "is a task-reading gate at least as good as a fixed rulebook", which the data can answer (it will show IBAC no worse, at the cost of a classifier call and its failures).

## Pending / follow-up

- Decide among the options above in #26.
- AgentDojo needs its own intent taxonomy and policy; the ToolPrivBench one does not carry over.
