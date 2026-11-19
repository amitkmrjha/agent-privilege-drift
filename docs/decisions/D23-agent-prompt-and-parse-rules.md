# D23: What the agent sees, and how unreadable replies are handled

- **Status:** Proposed (the author confirms before the pre-registration; the prompt text must be pre-registered in #29)
- **Date logged:** 2026-11-19
- **Related:** #17, #24, D06, D07

## Decision

1. **Tier hidden, prompt independent of it.** The prompt lists each tool's name, description and (when the benchmark has one) parameter schema. Nothing else. A test flips every tier and checks the prompt is byte-identical.
2. **Tool order is role-blind and fixed per scenario.** ToolPrivBench stores the three standard tools first, so file order would make "pick the first tool" look like good behaviour. Tools are listed ranked by SHA-256 of `(scenario id, tool name)`. The order is the same for every model, mediator, failure rate and seed, so cells stay comparable.
3. **No steering.** The prompt never says to prefer low privilege and never says a failure may be temporary. Both are what the experiment measures.
4. **One correction per step, then stop.** A reply with no action, bad JSON, an unknown tool, or both an Action and a Final Answer gets one re-prompt saying what was wrong (it does not suggest a tool). A second unreadable reply ends the run with `stop_reason = format_error`. Both attempts are recorded.
5. **An unknown tool is a parse error, not a proposed call.** A hallucinated tool name never reaches the mediator, so it cannot count as an escalation.
6. **Lenient parsing.** Case, bold markers, backticks, quotes, code fences, chatter after the JSON, and a missing or `None` input are all accepted, so formatting noise is not mistaken for behaviour. If a reply has several actions, only the first is used.
7. **Model-service errors are not behaviour.** Timeouts and connection errors propagate to the batch runner (#21); they are never written into a trace as agent steps.
8. **Stop sequence.** Every call sends `Observation:` as a stop sequence (D06), and any text after `Observation:` in a reply is discarded, so a model cannot supply its own tool result.

## Rationale

Each item removes a way the harness itself could change the measured behaviour. The step cap stays at 15 (D07) until the pilot (#24) shows whether it binds.

## Pending / follow-up

- The pilot (#24) must show the `format_error` rate and the `max_steps` rate are each under about 5 %, or the prompt needs fixing before pre-registration.
- Alternative for (2): vary the order by seed, which would average out position bias at the cost of extra variance between seeds. Settle in #26.
- The `intent` argument to the mediator is passed through unchanged (default `None`). IBAC (#20) classifies at `start_run`, so it owns the intent.
