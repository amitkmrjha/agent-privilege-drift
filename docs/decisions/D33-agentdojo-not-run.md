# D33: AgentDojo is not run (the secondary benchmark is left out of the registered study)

- **Status:** Accepted by the author (2026-11-21). Agreed with the supervisor.
- **Date logged:** 2026-11-21
- **Related:** #23, #34, #40, D08, D12, D26, D27, D31, `prereg/preregistration.md` (out of scope)

## What is decided

AgentDojo is **not part of the study**. No AgentDojo loader was built and no AgentDojo run was made. The
issues #23, #34 and #40 are closed as "not done, out of the registered scope". Attack success rate, which is
an AgentDojo measure, is not reported. D08 and D12 stay on record as designs that were not used.

## Why

1. **It was optional from the start.** The implementation plan named "drop the AgentDojo secondary grid" as
   reduction lever L2, and the three AgentDojo issues carried the `optional` and `P2` labels.
2. **It was the largest cost.** The plan sized the Llama AgentDojo grid at 4,050 runs plus 270 benign runs, with
   the longest prompts. The ToolPrivBench study alone took the time and the API budget that were available
   before 2 December.
3. **The registration left it out on purpose.** The pre-registration says AgentDojo is not part of it, and that
   if it is added later it gets its own pre-registration.

## What this costs the thesis

- ToolPrivBench cannot separate IBAC from MAC: the two are equal by construction on it (D26, D27). A contrast
  needs tasks whose required privilege differs, which AgentDojo's task suites have. RQ2 is therefore answered
  as "no difference between IBAC and MAC on this benchmark", and the IBAC claim is not tested where it could differ.
- State this in the scope and the limitations. Name AgentDojo as the next step in future work, with its own
  pre-registration.
- The proposal describes an AgentDojo part. It was not run, as agreed with the supervisor.

## If it is reopened

A new decision and a new pre-registration (not an edit of this one) before any AgentDojo run.
