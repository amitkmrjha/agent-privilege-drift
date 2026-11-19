# D26: What the MAC baseline is (reimplemented from the paper, simplified)

- **Status:** Proposed (the author confirms before pre-registration; the framing question below matters for RQ2)
- **Date logged:** 2026-11-19
- **Related:** #19, #20, #26, #38, D01, D04, D18

## What the paper says

Read on 2026-11-19 from the arXiv HTML of SEAgent (Ji et al., arXiv 2601.11893). **Caveat:** only the abstract to section 4.2 and the appendices from C onward were read verbatim. Sections 5 to 7 and Appendices A and B were available only as a model-generated summary, so the points marked (summary) are not verified.

- It is attribute-based (ABAC), not role-based. I found no role-to-tool matrix.
- Tools, agents and databases carry labels fixed before the run: for tools, object, action, sensitivity, privacy and integrality (verbatim, Appendix G). Tool labels come from an LLM plus human review (verbatim, Appendix F; Cohen's kappa 0.9456 on 80 tools).
- A policy is a goal (allow, deny or ask), a path pattern over a graph of who called what, and a rule over the attributes. At call time policies are tried most-specific first, the first match decides, and **the default is Allow** (verbatim, Algorithm 1).
- Labels are not derived from the user's task (summary). The access check is defined over the graph and was not evaluated without it.
- No code or policy-file link was found in the text read. The summary mentions an Open Science statement that I could not check.

## Decision

The MAC arm is a deliberately simple version of the same idea, as the PRD allows (M6, K1):

1. **A role is fixed before the run and never reads the task.** `configs/policies/mac_matrix.yaml` lists which tiers each role may call. Every scenario gets `default_role` (`standard_user`: tiers read_only and user) unless `scenario_roles` names another. That file is empty for the experiment.
2. **The check is the matrix, at call time.** A call is allowed exactly when the scenario's role may use the called tool's tier. Under D18 that means ToolPrivBench's `standard` tools (tier user) pass and its `risk` tools (tier admin) are blocked.
3. **The agent sees the one fixed block message** (D04); the telemetry keeps the reason, for example `MAC: role standard_user may not use tier admin`.
4. **Fail closed on an unlabelled tool**, where the paper's default is to allow. This cannot arise in the experiment, since the parser rejects tool names the scenario does not offer.
5. **Left out:** the information-flow graph and path-pattern policies (they target prompt injection and multi-agent messages, which ToolPrivBench has none of), the attributes other than tier, the "ask" goal, and LLM-assigned labels.

## Rationale

The experiment needs "a static, task-blind access policy" to compare against IBAC, which reads the task. The matrix gives exactly that, is testable case by case, and needs nothing the benchmark lacks.

## Pending / follow-up

- **A framing question for RQ2 (settle in #26).** The tiers are the benchmark's own ground truth, so this MAC arm separates `standard` from `risk` perfectly: it will block every violation and no legitimate call. IBAC can at best match it on violation rate. If that is the intended comparison, say so in the thesis: MAC is an upper bound for static labels. If the aim is a realistic baseline, the alternative is to give MAC imperfect labels, as the paper's own LLM-plus-human labelling does, but that adds a design choice I have not made.
- Read sections 5 to 7 and the Open Science statement (PDF) to confirm the points marked (summary) and to look for released policy files. `sources.md` says "no code"; that was checked only on arXiv metadata and GitHub search.
- The `read_only` and `administrator` roles are there for AgentDojo (#23) and for tests; the experiment uses `standard_user` only.
