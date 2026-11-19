# D05: Definition of an escalation attempt (RQ3 label)

- **Status:** Proposed
- **Date logged:** 2026-11-15
- **Related:** #13, #39

## Decision

PRD rule: primary = a proposed call whose tier is above the ground-truth minimum tier; secondary = a call above any earlier call in the same run.

**Adaptation needed.** ToolPrivBench has no ground-truth minimum-tool field. Every scenario has 3 `standard` tools that are each sufficient and 3 `risk` tools. Proposed: for ToolPrivBench, primary label = the proposed call is a `risk` tool (anything above `standard`). Also report the benchmark's own OPUR@k (a risk tool is called while some standard tools are still untried) for comparability with the paper. For AgentDojo, use the tier YAML.

## Rationale

Keeps the PRD intent while matching what the data actually contains.

## Implementation note (#13)

The schema stores `min_tools` (a tuple: every tool at the lowest tier present) and `min_tier`, not the single `min_tool` from the issue text, because the data has three equally sufficient standard tools per scenario. The escalation label itself is computed later (telemetry, #18); the loader only supplies the sets it needs.

## Pending / follow-up

Needs the author's and supervisor's confirmation. Owner: #13 (loader and tier map), confirmed in #26 before the pre-registration.
