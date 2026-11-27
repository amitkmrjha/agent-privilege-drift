# Sources: benchmarks and baselines

Verified on 2026-11-15 (issue #7). Status values: **verified** (exists and usable), **partial** (exists, gaps noted), **reimplement** (no usable code; fallback below).

## Summary

| Source | arXiv / URL | Licence | What it provides | Status |
|---|---|---|---|---|
| ToolPrivBench | arXiv 2606.20023; code https://github.com/AISafetyHub/agent-tool-selection-bias; data https://huggingface.co/datasets/BAAI/ToolPrivBench | Data: CC-BY-4.0 (Hugging Face card). Code: README says MIT but the repo has **no LICENSE file** and GitHub reports none | 544 scenarios (JSONL, ~2 MB), simulator, error injector, OPUR/PED metrics, prompts, SFT/RL data | **verified** (data and code available; gaps below) |
| SEAgent | arXiv 2601.11893 | n/a | Paper only. No code or data link in the arXiv metadata; no matching repo found on GitHub | **reimplement** |
| GrantBox | arXiv 2603.28166; code https://github.com/ZQ-Struggle/Agent-GrantBox | None declared (no LICENSE file) | Docker/MCP sandbox with real-world tools, ReAct and planning agents, dataset | **partial** (context only; not in the experiment grid) |
| BridgeScope | arXiv 2508.04031; code https://github.com/duoyw/bridgescope | None declared (no LICENSE file) | PostgreSQL MCP toolkit with privilege-aware tools, benchmark code | **partial** (context only; not in the experiment grid) |
| AgentDojo | https://github.com/ethz-spylab/agentdojo; PyPI `agentdojo` 0.1.35 (2025-10-27) | MIT | Task suites, injection tasks, pipeline and tool-runtime APIs | **verified** (secondary benchmark) |

## Preprint citation check

| ID | Title on arXiv | First author / date | Matches proposal citation? |
|---|---|---|---|
| 2606.20023 | When Lower Privileges Suffice: Investigating Over-Privileged Tool Selection in LLM Agents | Kaiyue Yang et al., 2026-06-18 | Exists. Compare against the proposal's reference list when writing Ch2. |
| 2601.11893 | Taming Various Privilege Escalation in LLM-Based Agent Systems: A Mandatory Access Control Framework | Zimo Ji et al., 2026-01-17 | Exists. Introduces SEAgent (MAC built on ABAC, information flow graph). |
| 2603.28166 | Evaluating Privilege Usage of Agents with Real-World Tools | Quan Zhang et al., 2026-03-30 | Exists. FSE 2026 IVR track. The repo README titles it "...on Real-World Tools" (minor wording difference). |
| 2508.04031 | BridgeScope: A Universal Toolkit for Bridging Large Language Models and Databases | Lianggui Weng et al., 2025-08-06 | Exists. 6 pages. |

All four IDs resolve on arXiv and the abstracts match how the PRD uses them. The ToolPrivBench README's BibTeX says `year = {2025}`, but the arXiv listing is June 2026; cite the arXiv year.

## ToolPrivBench: what it ships

Checked against `evaluation/data/goodcase_final/benchmark.jsonl` (544 lines, same count as the Hugging Face release).

| Item the plan needs | Present? | Detail |
|---|---|---|
| Scenario JSON | Yes | Fields: `scenario_id`, `type`, `domain`, `title`, `user_instruction`, `tools`. 544 unique IDs. |
| Domains / risk types | Yes | 8 domains (Database 83, Business 76, Education 72, Coding 67, Healthcare 65, Government 63, Media 62, Infrastructure 56). 5 risk types (Authority Escalation 139, Safety Bypass 116, Scope Expansion 99, Data Over-Exposure 99, Temporal Persistence 91). |
| Tool tier labels | **Binary only** | Every scenario has exactly 3 `standard` and 3 `risk` tools. There is **no read-only / user / admin tier**. |
| Ground-truth minimum tool | **No** | No field names a single correct tool. All 3 standard tools are independently sufficient by design. |
| Executable tool stubs | **No (canned strings)** | Tools have `name`, `description`, `success_output`, and for standard tools `simulation_error`; only 276 of 3,264 tools carry a `parameters` schema. The simulator returns the canned strings; nothing is executed. |
| Failure injection | Yes, but different from the PRD | `ErrorInjector` strategies: `first_attempt_fail`, `all_standard_fail`, `no_fail`. All 1,632 standard tools carry a `simulation_error`; no risk tool has a failure message (in 1,494 risk tools the field is absent, in the other 138, the 46 scenarios with typed `parameters`, it is an empty string; checked in #13). This is deterministic per-tool failure, not a probability-p HTTP 503 rate. |
| Metrics | Yes | OPUR@k and PED in `src/metrics/`. Over-privileged = a risk tool is called within `max_turns` before all 3 standard tools have been tried. |
| Doc/data consistency | Poor | `evaluation/data/README.md` documents `task_description`, `expected_behavior`, `risk_description`; the data uses `user_instruction` and has none of the other two. `schemas/scenario.json` requires `panic_logic`, which is absent from the data. Treat the data as authoritative. |

## Gaps and fallbacks

1. **No three-tier labels.** The PRD (M5) assumes tiers read-only / user / admin. Fallback: the loader (issue "Load both benchmarks into one schema") derives tiers: `standard` maps to the lower tier, `risk` to a higher tier, and a manual map is built for any finer split. Recorded as D18 in `docs/decisions/`.
2. **No ground-truth tool.** PoLP-violation is defined via standard-vs-risk roles (the benchmark's own OPUR rule), not a single minimum tool. Check PRD 1 §4.1 definitions against this.
3. **Failure injection differs.** The PRD injects HTTP 503 at three failure rates (the highest is p = 0.6, per lever L1). ToolPrivBench's `simulation_error` strings are scenario-specific (e.g. Jenkins agent offline). Fallback: the failure injector (own module) overrides tool output with a 503 at rate p and keeps the scenario `simulation_error` as an optional message variant. Log in the decisions file.
4. **Licence ambiguity.** Use the data under CC-BY-4.0 with attribution. For code, the README states MIT but no LICENSE file exists; do not vendor the code. Re-implement the (small) OPUR/PED logic and cite the paper. Ask the authors to add a LICENSE file (see email drafts).
5. **SEAgent has no code.** Fallback (already in PRD K1): reimplement MAC from the paper as a fixed role-to-tool matrix checked at call time, as scoped in the PRD. Read the paper's policy and ABAC attribute model before building it.
6. **GrantBox / BridgeScope** are related-work context. They are not in the 18-cell grid; no action beyond citation.

## AgentDojo (secondary benchmark)

- PyPI `agentdojo` 0.1.35, requires Python >= 3.10, MIT licence, repo active (last push 2026-11-15).
- Extension points relevant to decision D12 (custom pipeline element, injector wraps the tool runtime), from the docs at https://agentdojo.spylab.ai/api/agent_pipeline/basic_elements/ and `.../api/functions_runtime/`:
  - `BasePipelineElement.query(...)`: subclass to add a mediator or injector step.
  - `AgentPipeline`, `ToolsExecutor`, `ToolsExecutionLoop`: compose the loop.
  - `FunctionsRuntime.register_function` / `run_function`: wrap to inject failures at the tool boundary.
  - `ModelsEnum` includes `LOCAL` and `OPENAI_COMPATIBLE`, which should let a local Ollama Llama be used. To be confirmed in the AgentDojo spike (issue "Integrate AgentDojo").
- Not yet done: installing it and running one task. That belongs to the AgentDojo spike.

## Not done in this issue

- **Author emails (step 5).** Not sent; sending is outside what I was asked to do on your behalf. Drafts below. Record the date sent here once you send them.
- **SEAgent full-text check.** The PDF was downloaded but `pdftotext` is not installed here, so the paper body was not searched for a code link. Only arXiv metadata and GitHub search were checked. Worth a 2-minute manual look at the paper's abstract page and footnotes.

### Draft email: ToolPrivBench authors (licence)

> Subject: Licence file for agent-tool-selection-bias (ToolPrivBench)
>
> Dear Dr Yang and colleagues, I am an MS student at LJMU building a study that extends ToolPrivBench with probabilistic tool failures and access-control mediators. The repository README states MIT, but no LICENSE file is present. Could you add one, and confirm that using the 544 scenarios from `BAAI/ToolPrivBench` (CC-BY-4.0) with attribution is fine? Thank you for releasing the benchmark.

### Draft email: SEAgent authors (code)

> Subject: Code or policy files for SEAgent (arXiv 2601.11893)
>
> Dear Dr Ji and colleagues, I am an MS student at LJMU comparing access-control mediators for LLM agents. I could not find a public implementation of SEAgent. Is code, or the ABAC policy set used in your evaluation, available? If not, I plan to re-implement the MAC policy check from the paper and will cite it accordingly. Thank you.
