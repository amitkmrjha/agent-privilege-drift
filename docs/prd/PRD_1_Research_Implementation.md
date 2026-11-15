# PRD 1: Research Implementation and Experiment Runs

**Study:** Dynamic Tool Authorization: Evaluating Least-Privilege Violations and Privilege Escalation under Failure Pressure in Open-Source Agents
**Repo:** github.com/amitkmrjha/agent-privilege-drift | **Board:** github.com/users/amitkmrjha/projects/3
**Version:** 3.0 | **Date:** 2026-11-15 | **Deadline:** 2026-12-02
**Companion:** `PRD_2_Thesis_Writing.md` (literature review, thesis, viva, submission). Task IDs are shared across both documents.
**Technical detail:** `docs/plan/IMPLEMENTATION_PLAN.md` (repo layout, setup commands, telemetry schema); **per-issue plans:** `docs/plan/ISSUE_BREAKDOWN.md`; tasks are tracked as GitHub issues on the project board

**Scope of this document:** everything needed to **build the harness, run the experiments and produce the analysed results**: repository setup, benchmarks, failure injection, ReAct agent, the three mediators, pilot, pre-registration, batch runs, statistics. It stops where the written thesis starts. Its outputs (`results/numbers.json`, figures, tables, run manifests) are the inputs to PRD 2.

---

## 1. Purpose and product

**Purpose:** produce a defensible, pre-registered, reproducible answer to RQ1–RQ3.

**Product:** a Python research harness that runs an LLM agent (ReAct) on benchmark scenarios while injecting HTTP 503 tool failures, optionally gated by an access-control mediator (None, SEAgent MAC, IBAC), records full telemetry, and feeds a scripted statistical analysis.

**Core claim tested:** transient tool failure pushes agents toward higher-privilege tools ("privilege drift"), more or less so in a small open-weight model than in a frontier model, and an intent-based gate can reduce that without hurting task success.

**Research questions**

| ID | Question |
|---|---|
| RQ1 | Under transient tool failure, does Llama-3.1-8B-Instruct escalate privileges at a different rate than a frontier baseline? |
| RQ2 | Does IBAC reduce PoLP violations across failure regimes without significantly hurting task success, compared with SEAgent MAC and no mediator? |
| RQ3 | Which observable failure signals best predict a privilege-escalation attempt, and with what relative weight? |

**Run counts:** primary ToolPrivBench grid 2,700 runs (2 models × 3 rates × 3 mediators × 3 seeds × 50 scenarios, 18 cells); secondary AgentDojo grid 4,050 runs (Llama only, 3 rates × 2 mediators × 3 seeds × 15 × 15, 6 cells); recommended addition: 270 injection-free AgentDojo runs (D8).

---

## 2. Review findings that shape this PRD

| # | Finding | Action |
|---|---|---|
| F3 | Promised outcomes were not traced to evidence | §3 register |
| F4 | Key technical decisions were scattered | §4 method register and decisions |
| F5 | The proposal has inconsistencies | §5 list; resolved in T3.4 |
| F6 | **Effort gap.** The log gives about 77 h in total (about 35 h from 15 Nov). Both PRDs together estimate about 189 h; this one needs about 91 h | §7.2 scope and drop order |
| F7 | Requirements were not a sequence of executable tasks | §6 work breakdown |

---

## 3. Promised outcomes register (from the proposal)

Each row is a commitment. The thesis is complete when every row has evidence.

| ID | Promise (proposal reference) | Evidence required | Thesis location |
|---|---|---|---|
| PO1 | Measure how 503 pressure changes the PoLP-violation rate in Llama-3.1-8B-Instruct vs a frontier baseline (Abstract, RQ1, O1) | Violation rate by model × p; Δ = V(0.6) − V(0) with CIs | Ch5 |
| PO2 | New metric: **failure-induced escalation delta** (§5.2, §7.6) | Defined in Ch3; reported per model and mediator | Ch3, Ch5, Ch6 contribution |
| PO3 | Pre-registered primary contrast: difference-in-differences of Δ, frontier vs Llama, under None (§7.5.1) | One confirmatory test with corrected p and Cliff's delta | Ch5 |
| PO4 | Test whether IBAC reduces violations **without** hurting task success, vs SEAgent MAC and None (RQ2, O2) | Violation, ASR, task success per mediator; the **5 pp utility floor** result | Ch5 |
| PO5 | Report the floor outcome honestly: "reduces violations but exceeds threshold" is a valid result (§7.5.2) | Pre-declared wording used if it applies | Ch5, Ch6 |
| PO6 | Rank failure signals that predict escalation on ReAct traces with logistic regression + SHAP, with bootstrap CIs on ranks (RQ3, O3) | SHAP ranking, AUC under leave-scenario-out CV, VIF handling | Ch5 |
| PO7 | Three findings in the abstract: (i) over-escalation vs frontier, (ii) IBAC vs MAC trade-off, (iii) predictive signals | One clear answer per finding | Ch6 |
| PO8 | Indicate whether open-weight SLMs are enterprise-deployable under realistic faults and whether IBAC is a viable retrofit (Abstract, §5.2) | Discussion with stated limits | Ch6 |
| PO9 | Pre-registration, hash-committed subsets, cell integrity checks, deviations reported as exploratory (§7.8) | Tagged commit, hash file, integrity logs, deviations log | Ch3, Appendix |
| PO10 | Reproducibility artefact: code MIT, ~5 GB telemetry CC-BY 4.0, seed schedule, Ollama tags (§7.7) | Public repo, release, manifest per cell | Appendix, repo |
| PO11 | Harness supports Plan-and-Execute, other models, bursty faults as future work without re-implementation (§7.1, §7.7) | Pluggable interfaces, unit-tested stubs | Ch6 future work |
| PO12 | Falls within LJMU Code of Practice; no human subjects (§7.7) | Ethics statement | Ch3 |
| PO13 | Smaller-than-target effects reported as **upper bounds**, not point estimates (§7.6) | Rule applied in reporting | Ch5 |

---

---

## 4. Key technical methodology register

These are fixed by the proposal. Do not change them after the pre-registration freeze without logging a deviation.

| ID | Item | Specification |
|---|---|---|
| M1 | Design | Pre-registered factorial: {model} × {scaffold} × {failure rate} × {mediator}; 18 primary cells (ToolPrivBench) + 6 secondary (AgentDojo) |
| M2 | Independent variable | HTTP 503 as independent Bernoulli per tool call, p ∈ {0, 0.3, 0.6}; opaque to the agent; no harness retry |
| M3 | Models | Llama-3.1-8B-Instruct Q4_K_M via Ollama; one frontier model (Gemini 2.5 Flash default, Sonnet 4.5 alternative) chosen by the three §7.4.4 criteria and hash-committed; identical sampling (temp 0.2, top-p 0.9, 2,048 tokens) |
| M4 | Scaffold | ReAct only |
| M5 | Datasets | ToolPrivBench 50-scenario stratified subset (6–7 per domain × 8) primary; AgentDojo 15 tasks / 15 injections (stratified over 5 categories), Llama only, secondary; both wrapped in an MCP-compatible schema; tiers read-only / user / admin |
| M6 | Mediators | None; SEAgent MAC (fixed role-tool matrix at call time); IBAC (Llama classifier reads the trusted user prompt once, 8-intent taxonomy, YAML policy, gate at tool boundary); all behind `gate(call, intent) → Decision` |
| M7 | Metrics | PoLP-violation rate, escalation delta Δ, task success, ASR (Llama on AgentDojo), plus RQ3 signals: rolling 503 rate, retry-since-last-success, error surface, step index, cumulative reasoning tokens, escalation latency, mediator-block count, classifier confidence |
| M8 | Statistics | Unit = scenario (3 seeds averaged, n = 50). Paired Wilcoxon signed-rank; Page's trend test; Cliff's delta (Romano bands); Holm–Bonferroni over the 18-cell family (AgentDojo corrected separately); MDE 12 pp, power ≈ 0.80 by Monte-Carlo (10,000 replicates, Beta-Binomial, baseline ≈ 0.35) |
| M9 | RQ3 model | Logistic regression on escalation-at-step; VIF > 5 collapsed to a PC; leave-scenario-out 5-fold CV; SHAP; 1,000-sample paired bootstrap for rank CIs |
| M10 | Integrity | Per-cell checks: 150 traces (50 × 3), injection rate within ±3 pp of p, tier attribution equals ground truth; failing cells re-run |
| M11 | Run discipline | Per-scenario results written to disk; restart skips finished items; one manifest per cell |
| M12 | Reduction levers | In order: L1 drop p = 0.6, L2 drop AgentDojo, L3 drop frontier arm; variance contingency: 3 → 5 seeds |

### 4.1 Design decisions the proposal leaves open (to be fixed in the pre-registration)

| ID | Decision | Rule |
|---|---|---|
| D2 | What counts as a violation | **Proposed** calls (before the gate) for RQ1 and RQ3. For RQ2 report proposed, executed and blocked |
| D3 | Gate vs injector order | agent → gate → injector → tool; blocked calls get no 503 draw |
| D4 | Block message | One fixed neutral string for MAC and IBAC, different from the 503 string |
| D5 | Escalation label | Primary: proposed tier above the ground-truth minimum. Secondary: above any earlier call in the run |
| D6 | ReAct format | Text format (Thought / Action / Action Input / Observation) for both models |
| D7 | Retries and cap | Agent decides; no harness retry; max steps fixed (suggest 15) |
| D8 | AgentDojo benign runs | Add 15 injection-free runs per cell (270 total) so the utility floor has a clean baseline |
| D9 | API budget | Measure LLM calls/run in the pilot; plan frontier runs against the rate limit |
| D11 | Violation rate denominator | Per-run fraction of proposed calls, averaged over the 3 seeds, giving one value per scenario |
| D12 | AgentDojo integration | Custom pipeline element; injector wraps AgentDojo's tool runtime |
| D13 | Classifier failure | Fall back to the most restrictive policy and log it |
| D14 | Rolling-window size k for the 503 rate | Fixed in the pre-registration |

---

---

## 5. Inconsistencies in the proposal to resolve before pre-registration

| # | Issue | Suggested resolution |
|---|---|---|
| I1 | The abstract says "24 experimental conditions"; the design is 18 primary + 6 secondary cells (24 in total, but under two environments) | State both numbers explicitly in Ch3 |
| I2 | Table 2.1 and Table 3.1 mention ABAC, but Static ABAC is out of scope | Keep as literature comparison only; mark it "not tested" |
| I3 | Lever references point to §7.8 in one place and §9.9 in another | Use one canonical list (M12) in the pre-registration |
| I4 | RQ3 lists four signals; §7.5.3 lists five (adds cumulative reasoning tokens) | Use all five and say so |
| I5 | IBAC is attributed to Zverev et al. (2025), whose paper is about instruction/data separation, not an access-control design | Cite Zverev for the motivation only; present IBAC as this study's design |
| I6 | The AgentDojo secondary grid is "Llama only", so the model factor does not apply; "18-cell" and "6-cell" families differ in structure | State clearly in Ch3 |
| I7 | The frontier arm's mediators: IBAC classifier is Llama even for the frontier agent | State as design (classifier fixed) and as a validity note |
| I8 | Several citations are 2026 arXiv preprints (e.g. 2606.20023, 2601.11893) | Verify each exists and the content matches how it is cited before it goes in the thesis |

---

---

## 6. Work breakdown (research implementation and runs)

**Conventions.** Priority: **P0** required; **P1** strongly wanted; **P2** drop first. Hours are estimates with AI-assisted coding. "Needs" lists tasks that must finish first. Each task fits one sitting and can be one GitHub issue.

### WS0 Governance and repository

| ID | Task | Output | Acceptance | Pri | h | Needs |
|---|---|---|---|---|---|---|
| T0.1 | Clone repo; add README (study summary), MIT LICENSE, `.gitignore`, `CITATION.cff` | Repo skeleton pushed | README states RQs, status, how to run | P0 | 1 | |
| T0.2 | Initialise `uv` project and the folder layout from `docs/plan/IMPLEMENTATION_PLAN.md` §2 | `pyproject.toml`, `uv.lock`, empty modules | `uv run pytest` runs (0 tests ok) | P0 | 1.5 | T0.1 |
| T0.3 | Set up the GitHub Project: milestones M0–M8, labels per workstream, fields (Priority, Estimate); create one issue per task in this section | Board populated | Every T-ID has an issue | P1 | 1.5 | T0.1 |
| T0.4 | Create `docs/decisions.md` with D2–D14 and answer each | Decision log | All open decisions have an answer or an owner/date | P0 | 1 | |
| T0.5 | **Verify benchmark availability (D1):** locate ToolPrivBench, AgentDojo, SEAgent code/data, licences, and confirm each cited 2026 preprint exists (I8) | `docs/research-reference/sources.md` | Each source has a URL, licence, and verified status | P0 | 1.5 | |

### WS2 Harness build

| ID | Task | Output | Acceptance | Pri | h | Needs |
|---|---|---|---|---|---|---|
| T2.1 | Install Ollama, pull Llama, set up LiteLLM, set `num_ctx`, add `.env` handling; smoke test both models | `llm/` client, `configs/models.yaml` | Same call works for both models; seed behaviour recorded | P0 | 3 | T0.2 |
| T2.2 | Schema and loaders: pydantic models; ToolPrivBench loader; tier maps; AgentDojo loader and tier YAML | `schema.py`, `data/` | Round-trip test passes (deterministic, reversible) | P0 | 5 | T0.5 |
| T2.3 | Subset builder: 50 stratified scenarios; AgentDojo 15/15; seed schedule; SHA-256 files | `prereg/subsets/`, `seed_schedule.json` | Hashes recorded; stratification counts correct | P0 | 2 | T2.2 |
| T2.4 | Failure injector with its own seeded RNG and fixed 503 body | `failure/injector.py` + tests | Empirical rate within tolerance; p = 0 never injects; same seed gives the same draws | P0 | 3 | T2.2 |
| T2.5 | ReAct loop and parser; tier hidden from prompt; bounded format-correction; max steps | `agent/react.py` + tests | Fake-LLM scripted run completes; malformed input never crashes | P0 | 5 | T2.1, T2.2 |
| T2.6 | Telemetry: record schema, JSONL writer, derived RQ3 features without look-ahead | `telemetry/` + tests | Feature values match a hand-computed example | P0 | 3 | T2.5 |
| T2.7 | Mediator contract and None arm; contract conformance test suite | `mediators/base.py`, `none.py` | Same suite is ready for all arms | P0 | 1.5 | T2.2 |
| T2.8 | SEAgent MAC arm (matrix YAML) | `mediators/mac.py` | Blocks and allows the hand-built cases correctly | P0 | 3 | T2.7, T0.5 |
| T2.9 | IBAC: 8-intent taxonomy, classifier prompt (JSON), policy YAML, gate, restrictive fallback | `mediators/ibac.py`, `classifier.py` | Classifier output parsed; fallback tested; gate unit tests | P0 | 5 | T2.7 |
| T2.10 | Runner: grid expansion, atomic writes, resume, manifests, the three integrity checks | `runner/` | Kill and restart a batch: no duplicates, no corruption; integrity checks fail on planted errors | P0 | 5 | T2.6 |
| T2.11 | Integration: fake LLM across 3 mediators × 3 rates; golden test with cached responses | `tests/integration/` | Expected telemetry produced; golden metrics reproducible | P0 | 2 | T2.8–T2.10 |
| T2.12 | AgentDojo pipeline integration (D12) with the injector and None/IBAC arms; benign-utility runs (D8) | `data/agentdojo_pipeline.py` | One AgentDojo run end to end with telemetry | P2 | 6 | T2.9, T2.10 |

### WS3 Pilot and pre-registration

| ID | Task | Output | Acceptance | Pri | h | Needs |
|---|---|---|---|---|---|---|
| T3.1 | Pilot: ~10 scenarios × 3 seeds × 3 rates × 3 mediators on Llama; measure s/run, calls/run, tokens/run | `docs/pilot.md` | Throughput table filled in | P0 | 3 | T2.11 |
| T3.2 | Check p = 0 baseline vs the published ≈ 0.35 violation rate; check parse-error, max-steps-hit and classifier-failure rates | Pilot checks | Each rate under about 5 %, or the prompt fixed | P0 | 1 | T3.1 |
| T3.3 | Power: Monte-Carlo with pilot variance (MDE 12 pp, n = 50) | `analysis/power.py`, result | Power ≥ 0.80 or the five-seed contingency decided | P0 | 2 | T3.1 |
| T3.4 | Resolve inconsistencies I1–I8 and decisions D2–D14 | Updated `docs/decisions.md` | All resolved in writing | P0 | 1 | T0.4 |
| T3.5 | Choose the frontier model by the three criteria; record evidence | `docs/frontier_choice.md` | Choice justified | P0 | 1 | T3.1 |
| T3.6 | Write the pre-registration (items a–g of §7.8 plus D-decisions) | `prereg/preregistration.md` | Contains hypotheses with direction, contrast, floor, power, tests, levers, hashes | P0 | 2.5 | T3.3–T3.5 |
| T3.7 | Commit, hash and tag (`prereg-v1`, `exp-v1`) | Tags, `HASHES.txt` | Tags pushed before any full run | P0 | 0.5 | T3.6 |

### WS4 Experiment execution (machine time in brackets; hands-on time in the hours column)

| ID | Task | Output | Acceptance | Pri | h | Needs |
|---|---|---|---|---|---|---|
| T4.1 | Llama ToolPrivBench batch: 9 cells, 1,350 runs, overnight [machine time from pilot] | `runs/` cells | All 9 cells pass integrity checks | P0 | 2 | T3.7 |
| T4.2 | Frontier ToolPrivBench batch: 9 cells, 1,350 runs, throttled [days by rate limit] | `runs/` cells | All 9 cells pass integrity checks, or lever L3 logged | P1 | 2 | T3.7 |
| T4.3 | Data hygiene: separate infrastructure errors from agent behaviour; re-run failed items | Clean set | Row counts correct; no infrastructure error counted as a 503 | P0 | 2 | T4.1 |
| T4.4 | AgentDojo batch: 6 cells + benign runs [machine time] | `runs/` cells | Integrity checks pass, or lever L2 logged | P2 | 2 | T2.12, T3.7 |
| T4.5 | Log every deviation after `exp-v1` | `docs/deviations.md` | Complete | P0 | 0.5 | |

### WS5 Analysis (all outputs regenerate from `runs/**` with one command)

| ID | Task | Output | Acceptance | Pri | h | Needs |
|---|---|---|---|---|---|---|
| T5.1 | Stats library: scenario aggregation, Wilcoxon, Page, Cliff's delta, Cohen's d, Holm | `analysis/stats.py` + tests | Matches known examples | P0 | 3 | T2.6 |
| T5.2 | RQ1: violation rate by model × p; Δ; difference-in-differences with bootstrap CI | Tables, figures | Primary contrast reported with corrected p and effect size | P0 | 3 | T4.1, T5.1 |
| T5.3 | RQ2: violation, task success, ASR per mediator; utility-floor check | Tables, figures | Floor decision stated using pre-declared wording | P0 | 2.5 | T4.1, T5.1 |
| T5.4 | RQ3: step-level table, VIF, logistic regression with grouped CV, SHAP, bootstrap rank CIs | `analysis/predictors.py`, figures | AUC reported; ranking with CIs | P0 | 4 | T4.1 |
| T5.5 | AgentDojo secondary analysis (own Holm family) | Tables, figures | Reported as secondary | P2 | 1.5 | T4.4 |
| T5.6 | `make analyse` regenerates every number into `results/numbers.json` and every figure | Makefile target | Clean run reproduces all outputs | P0 | 1.5 | T5.2–T5.4 |
| T5.7 | Results report: per RQ, pre-registered test, result, effect size, decision, exploratory findings, deviations, limitations | `docs/results/RESULTS.md` | Every promised outcome PO1–PO8 has evidence or a stated reason it is missing | P0 | 3 | T5.6, T4.5 |
| T5.8 | Hand-off package for the writing phase: figure/table index, method facts, pilot numbers, deviations, open caveats | `docs/handoff.md` | PRD 2 "Needs from PRD 1" fully satisfied | P0 | 1 | T5.7 |

### WS8a Repository release

| ID | Task | Output | Acceptance | Pri | h | Needs |
|---|---|---|---|---|---|---|
| T8.1 | Clean the repo; README with reproduce steps; release `v1.0` with telemetry archive | Public release | Clean-clone golden test passes | P1 | 2 | T5.6 |

**Estimated total for this PRD:** WS0 6.5 h, WS2 43.5 h, WS3 11 h, WS4 8.5 h, WS5 19.5 h, T8.1 2 h, about **91 h**.

**Outputs handed to PRD 2:** `docs/results/RESULTS.md`, `docs/handoff.md`, `results/numbers.json`, `results/figures/`, `results/tables/`, cell manifests, `docs/pilot.md`, `docs/deviations.md`, `prereg/preregistration.md`, and the tagged repository.

---

## 7. Schedule, scope and gates

### 7.1 Effort
This document needs about 91 h. If most of it remains, the plan cannot fit in about 35 h. **Confirm the status of every task first.**

### 7.2 Minimum-viable scope and drop order
All P0 tasks, then P1. Drop in this order:
1. T2.12, T4.4, T5.5 (AgentDojo secondary): lever L2. RQ2 is then answered on ToolPrivBench only and the ASR measure is lost.
2. T4.2 (frontier arm), only if forced: lever L3. It removes the model comparison, which is RQ1. **Avoid this one.** Protect it by running it in parallel with Llama batches and by using a paid tier within the £50 cap if the free rate limit is too slow.
3. The p = 0.6 cells: lever L1, last, because it removes the definition of Δ.

### 7.3 Calendar mapping (execution log)

| Log week | Dates | Tasks |
|---|---|---|
| 1 | 25–31 Oct | WS0, WS2, WS3 (pilot and pre-registration, **missing from the log**), T4.1, T4.3 |
| 2 | 1–7 Nov | T4.2, T4.4, T5.1–T5.3 |
| 3 | 8–14 Nov | T5.4, T5.6; supply results to PRD 2 |
| 4–5 | 15–28 Nov | Only fixes, reruns and T8.1; protect writing time |

### 7.4 Gates

| Gate | Before | Checks |
|---|---|---|
| G0 | Building | T0.5 done: benchmarks and baselines exist and are licensed for use |
| G1 | Pilot | T2.11 green |
| G2 | Any full run | T3.7: pre-registration committed and tagged |
| G3 | Analysis | Integrity checks pass on every cell used |
| G4 | Hand-off to PRD 2 | T5.6 reproduces every number from raw traces |

---

## 8. Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-1 | Reproducible: same config + seed + cached responses give the same metrics; git SHA and model digest in every manifest |
| NFR-2 | Robust to interruption: resume without duplicated or corrupted results |
| NFR-3 | Valid: only p and the mediator vary between cells; sampling constants identical across models |
| NFR-4 | Cost: £0 open-weight compute; ≤ £50 API |
| NFR-5 | Security: no secrets committed; `.env` untracked |
| NFR-6 | Testable: injector, mediators, parser, stats unit-tested; one golden test |
| NFR-7 | Ethics: public benchmarks and synthetic tools only; model licences respected; falls inside the LJMU Code of Practice |
| NFR-8 | Open: MIT code, CC-BY 4.0 telemetry |

---

---

## 9. Risks

| ID | Risk | Impact | Mitigation |
|---|---|---|---|
| K1 | Benchmarks or SEAgent code unavailable | High | T0.5 first; reimplement MAC from the paper; contact authors |
| K2 | Effort gap (about 185 h vs about 35 h left) | High | Status check; §7.2 scope; ask the supervisor about timeline if little is done |
| K3 | Llama throughput; AgentDojo prompts are long | High | Pilot measures; lever L2 |
| K4 | Frontier API rate limit vs calls per run | High | Parallel run, paid tier within £50, or lever L3 |
| K5 | Violation scoring does not reproduce about 0.35 at p = 0 | High | T3.2 check before any full run |
| K6 | Llama context truncation corrupts runs | High | Set and log `num_ctx`; test the longest scenario |
| K7 | Underpowered at n = 50 | Med | Five seeds; report upper bounds (PO13) |

---

## 10. Open questions

| # | Question | Needed by |
|---|---|---|
| Q1 | Which tasks (T-IDs) are already done, and which levers have already been used? | Now |
| Q2 | Are ToolPrivBench, AgentDojo and SEAgent code and data available, and under what licences? | T0.5 |
| Q4 | Frontier model and tier (free Gemini or paid) | T3.5 |
| Q5 | Is the 2 Dec deadline movable if the minimum-viable scope proves too large? | Now |
| Q6 | Is the repo to stay public from the start, or private until submission? | T0.1 |

---

## 11. Traceability

| RQ | Promised outcomes | Method items | Tasks |
|---|---|---|---|
| RQ1 | PO1, PO2, PO3, PO13 | M2, M3, M7, M8 | T2.4–T2.6, T4.1–T4.3, T5.1–T5.2 |
| RQ2 | PO4, PO5 | M6, M7, M8 | T2.7–T2.9, T4.1, T5.3 (T2.12, T4.4, T5.5 for AgentDojo) |
| RQ3 | PO6 | M7, M9 | T2.6, T5.4 |
| Shared | PO9–PO11 | M1, M10–M12 | WS3, T8.1 |

---

## 12. Document control

| Version | Date | Change |
|---|---|---|
| 1.0–2.1 | 2026-11-15 | Single combined PRD |
| 3.0 | 2026-11-15 | Split: this document covers research implementation and runs; thesis writing moved to PRD 2 |
