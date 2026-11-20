# Design decisions

One short file per decision. D01 to D14 come from `docs/plan/IMPLEMENTATION_PLAN.md` section 1 and `docs/prd/PRD_1_Research_Implementation.md` section 4.1; D15 onwards were made while building the repository. All decisions in the **Proposed** or **Pending** state must be settled in the issue "Resolve the open design decisions" (#26) before the pre-registration is tagged (gate G2). Logged 2026-11-15.

Status meanings: **Accepted** = rule taken from the PRD or made and done; **Proposed** = a suggested adaptation that needs the author's confirmation; **Pending the pilot** = cannot be decided until pilot data exists; **Resolved** = answered by evidence.

| ID | Decision | Status | Related |
|---|---|---|---|
| D01 | [Are the benchmarks and baselines obtainable?](D01-source-availability.md) | Resolved | #7 |
| D02 | [What counts as a violation](D02-violation-definition.md) | Accepted | #18, #38 |
| D03 | [Order of mediator gate and failure injector](D03-gate-injector-order.md) | Accepted | #15, #16 |
| D04 | [What the agent sees when a call is blocked](D04-block-message.md) | Accepted | #15, #19, #20 |
| D05 | [Definition of an escalation attempt (RQ3 label)](D05-escalation-label.md) | Proposed | #13, #39 |
| D06 | [ReAct format](D06-react-format.md) | Accepted | #17 |
| D07 | [Retry policy and step cap](D07-retries-and-step-cap.md) | Accepted (pilot: 15 not binding; keep 15, needs confirming) | #17, #24 |
| D08 | [AgentDojo benign-utility runs](D08-agentdojo-benign-runs.md) | Accepted (only if AgentDojo is kept) | #23, #34 |
| D09 | [API call budget versus rate limit](D09-api-budget.md) | Pending the pilot | #24, #28, #32 |
| D10 | [Seed schedule versus common random numbers](D10-seed-schedule.md) | Accepted | #14 |
| D11 | [What the violation rate divides by](D11-violation-rate-denominator.md) | Accepted | #36, #37 |
| D12 | [How AgentDojo is integrated](D12-agentdojo-integration.md) | Accepted (only if AgentDojo is kept) | #23 |
| D13 | [IBAC classifier failure](D13-classifier-failure.md) | Accepted | #20 |
| D14 | [Rolling-window size k for the 503 rate](D14-rolling-window-size.md) | Pilot done; k = 3 recommended, needs confirming | #18, #39, #26 |
| D15 | [Python package name](D15-package-name.md) | Accepted (done) | PR #49 |
| D16 | [Ollama runs natively, not in Docker](D16-native-ollama.md) | Accepted (done) | PR #50 |
| D17 | [No automated dependency updates](D17-no-dependabot.md) | Accepted (done) | PR #50 |
| D18 | [Tier map for ToolPrivBench](D18-toolprivbench-tier-map.md) | Proposed | #13, #19, #20 |
| D19 | [Which tools receive injected 503s](D19-failure-injection-scope.md) | Proposed (built as proposed, needs confirming) | #16 |
| D20 | [Run the open model first, repeat with the frontier model later](D20-staged-execution.md) | Accepted | #12, #28, #29, #31, #32 |
| D21 | [How the subset is drawn and how seeds are dealt](D21-subset-and-seed-method.md) | Proposed | #14, #29 |
| D22 | [How the failure draws are made](D22-failure-draw-method.md) | Proposed | #16, #21 |
| D23 | [What the agent sees, and how unreadable replies are handled](D23-agent-prompt-and-parse-rules.md) | Proposed | #17, #24, #29 |
| D24 | [How the telemetry fields are defined](D24-telemetry-definitions.md) | Accepted (`k` pending the pilot) | #18, #26, #39 |
| D25 | [How the batch runner resumes, retries and checks](D25-batch-runner-rules.md) | Proposed | #21, #22, #29 |
| D26 | [What the MAC baseline is (reimplemented from the paper, simplified)](D26-mac-baseline.md) | Proposed | #19, #20, #26, #38 |
| D27 | [How IBAC is built, and what it can and cannot separate](D27-ibac-design.md) | Proposed (finding needs a decision) | #20, #23, #26, #38 |
| D28 | [Frontier model id, and sampling settings the frontier API rejects](D28-frontier-model-id-and-sampling.md) | Proposed (model id provisional) | #26, #28 |
| D29 | [Which violation measure is primary (rate per call, or violating calls per run)](D29-primary-violation-measure.md) | Proposed (raised by the pilot) | #26, #27, #29, #37 |
| D30 | [Seeds per scenario (3 or 5)](D30-seeds-per-scenario.md) | Accepted: keep 3 (departs from the plan's rule; consequences recorded) | #26, #27, #29 |
| D31 | [Which cells are run, and in what order](D31-run-plan.md) | Proposed (9 of 18 cells; needs the supervisor) | #26, #29, #31, #32 |
