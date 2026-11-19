# D18: Tier map for ToolPrivBench

- **Status:** Proposed
- **Date logged:** 2026-11-15
- **Related:** #13, #19, #20

## Decision

PRD M5 assumes three tiers (read-only / user / admin). ToolPrivBench has two roles. Proposed: for ToolPrivBench use the two roles as the tiers (`standard` = low, `risk` = high) and keep the three-tier scheme for AgentDojo.

## Rationale

Deriving a finer split would be a judgement on 3,264 tool descriptions and would be hard to defend.

## Implementation note (#13)

`configs/tiers/toolprivbench_tiers.yaml` maps `standard` to tier `user` and `risk` to tier `admin`. `standard` is not `read_only` because those tools change state. Only the order of the tiers is analysed, so this label choice does not affect any result. The map must be one-to-one, which lets the loader convert a scenario back to its raw form exactly (round-trip test on all 544 scenarios).

## Pending / follow-up

Needs the author's confirmation. It also shapes the MAC role-tool matrix (#19) and the IBAC policy (#20).
