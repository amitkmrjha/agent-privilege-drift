# Design decisions

One short file per decision. D01 to D14 were made during planning, before the build; D15 onwards were made while building the repository. All decisions in the **Proposed** or **Pending** state must be settled in the issue "Resolve the open design decisions" (#26) before the pre-registration is tagged (gate G2). Logged 2026-11-15.

Status meanings: **Accepted** = rule taken from the PRD or made and done; **Proposed** = a suggested adaptation that needs the author's confirmation; **Pending the pilot** = cannot be decided until pilot data exists; **Resolved** = answered by evidence.

| ID | Decision | Status | Related |
|---|---|---|---|
| D01 | [Are the benchmarks and baselines obtainable?](D01-source-availability.md) | Resolved | #7 |
| D02 | [What counts as a violation](D02-violation-definition.md) | Accepted | #18, #38 |
| D03 | [Order of mediator gate and failure injector](D03-gate-injector-order.md) | Accepted | #15, #16 |
| D04 | [What the agent sees when a call is blocked](D04-block-message.md) | Accepted | #15, #19, #20 |
| D05 | [Definition of an escalation attempt (RQ3 label)](D05-escalation-label.md) | Accepted (2026-11-21) | #13, #39 |
| D06 | [ReAct format](D06-react-format.md) | Accepted | #17 |
| D07 | [Retry policy and step cap](D07-retries-and-step-cap.md) | Accepted (2026-11-21) | #17, #24 |
| D08 | [AgentDojo benign-utility runs](D08-agentdojo-benign-runs.md) | Accepted (only if AgentDojo is kept) | #23, #34 |
| D09 | [API call budget versus rate limit](D09-api-budget.md) | Accepted (2026-11-21); quota read at run time | #24, #28, #32 |
| D10 | [Seed schedule versus common random numbers](D10-seed-schedule.md) | Accepted | #14 |
| D11 | [What the violation rate divides by](D11-violation-rate-denominator.md) | Accepted | #36, #37 |
| D12 | [How AgentDojo is integrated](D12-agentdojo-integration.md) | Accepted (only if AgentDojo is kept) | #23 |
| D13 | [IBAC classifier failure](D13-classifier-failure.md) | Accepted | #20 |
| D14 | [Rolling-window size k for the 503 rate](D14-rolling-window-size.md) | Accepted (2026-11-21) | #18, #39, #26 |
| D15 | [Python package name](D15-package-name.md) | Accepted (done) | PR #49 |
| D16 | [Ollama runs natively, not in Docker](D16-native-ollama.md) | Accepted (done) | PR #50 |
| D17 | [No automated dependency updates](D17-no-dependabot.md) | Accepted (done) | PR #50 |
| D18 | [Tier map for ToolPrivBench](D18-toolprivbench-tier-map.md) | Accepted (2026-11-21) | #13, #19, #20 |
| D19 | [Which tools receive injected 503s](D19-failure-injection-scope.md) | Accepted (2026-11-21) | #16 |
| D20 | [Run the open model first, repeat with the frontier model later](D20-staged-execution.md) | Accepted | #12, #28, #29, #31, #32 |
| D21 | [How the subset is drawn and how seeds are dealt](D21-subset-and-seed-method.md) | Accepted (2026-11-21) | #14, #29 |
| D22 | [How the failure draws are made](D22-failure-draw-method.md) | Accepted (2026-11-21) | #16, #21 |
| D23 | [What the agent sees, and how unreadable replies are handled](D23-agent-prompt-and-parse-rules.md) | Accepted (2026-11-21) | #17, #24, #29 |
| D24 | [How the telemetry fields are defined](D24-telemetry-definitions.md) | Accepted (`k` pending the pilot) | #18, #26, #39 |
| D25 | [How the batch runner resumes, retries and checks](D25-batch-runner-rules.md) | Accepted (2026-11-21) | #21, #22, #29 |
| D26 | [What the MAC baseline is (reimplemented from the paper, simplified)](D26-mac-baseline.md) | Accepted (2026-11-21) | #19, #20, #26, #38 |
| D27 | [How IBAC is built, and what it can and cannot separate](D27-ibac-design.md) | Accepted (2026-11-21) | #20, #23, #26, #38 |
| D28 | [Frontier model id, and sampling settings the frontier API rejects](D28-frontier-model-id-and-sampling.md) | Accepted (2026-11-21) | #26, #28 |
| D29 | [Which violation measure is primary (rate per call, or violating calls per run)](D29-primary-violation-measure.md) | Accepted (2026-11-21) | #26, #27, #29, #37 |
| D30 | [Seeds per scenario (3 or 5)](D30-seeds-per-scenario.md) | Accepted: keep 3 (departs from the plan's rule; consequences recorded) | #26, #27, #29 |
| D31 | [Which cells are registered, and in what order they are run](D31-run-plan.md) | Accepted by the author: the full 18-cell grid in two priority-ordered lanes; mitigation (cut from the end) decided later, pre-declared | #26, #29, #31, #32 |
| D32 | [Amendment exp-v2: add a large frontier model (Gemini 4 Carbon), after the exp-v1 results](D32-exp-v2-large-frontier-model.md) | Proposed (2026-11-21); accepted at the exp-v2 freeze | #28, #30 |
| D33 | [AgentDojo is not run (left out of the registered study)](D33-agentdojo-not-run.md) | Accepted (2026-11-21) | #23, #34, #40 |
