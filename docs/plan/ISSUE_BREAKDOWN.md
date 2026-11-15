# Issue Breakdown: project setup to documented results

Companion to `docs/prd/PRD_1_Research_Implementation.md` (what and why) and `docs/plan/IMPLEMENTATION_PLAN.md` (technical layout).
This file is the **plan for each individual issue**: every task becomes one GitHub issue with the steps, files, acceptance test and estimate below. The next phase, thesis writing, is covered by `docs/prd/PRD_2_Thesis_Writing.md` and starts only after Phase 5 here.

---

## 1. How the issues are organised on GitHub

### 1.1 Plain titles, no ID codes
Every issue title is a short plain phrase that says what gets done (for example "Build the failure injector"). No codes such as T2.4 appear in titles, branches or issue text. The PRDs keep their internal reference codes, and the mapping is at the end of this file (§4).

### 1.2 Phases are parent issues; tasks are sub-issues
There is one **parent issue per phase**. Each task issue is a **sub-issue** of its phase. The "Sub-issues progress" field on the project board shows how far each phase is.

| Parent issue (phase) | Sub-issues | Ends when | Gate |
|---|---|---|---|
| Phase 0: Project setup | 5 | Repo builds, sources verified, decisions logged | G0 |
| Phase 1: Harness build | 11 (+ "Integrate AgentDojo" if kept) | Fake-model integration and golden tests pass | G1 |
| Phase 2: Pilot and pre-registration | 7 | Pre-registration and code freeze tagged | G2 |
| Phase 3: Experiment runs | 4 (+ "Run the AgentDojo batch" if kept) | Every cell passes integrity checks | G3 |
| Phase 4: Analysis | 5 (+ "Analyse the AgentDojo results" if kept) | One command reproduces every number | G4 |
| Phase 5: Document the outcome | 3 | Results report, hand-off package and release done | G5 |

The next phase, thesis writing (`docs/prd/PRD_2_Thesis_Writing.md`), starts after Phase 5.

### 1.3 Dependencies use GitHub's issue relationships, not text
Each issue's **Blocked by** list below is entered as a native "Blocked by" relationship on the issue (the reverse shows as "Blocking"). Do not write dependencies in the issue body.

Rules:
- A "Blocked by" entry means the work cannot start until that issue is closed.
- Soft ordering goes in a comment, not a relationship.
- Issues that carry optional AgentDojo work are marked **(optional)**. If AgentDojo is dropped, close them as "not planned" and the blockers clear. The same applies to "Run the frontier ToolPrivBench batch" if the frontier arm is dropped (reduction lever L3). Log either choice in the deviations log.
- Analyses are blocked by "Clean and freeze the run data", never by a raw batch.

### 1.4 What to work on next
Pick any open issue that is not blocked, highest priority first, then earliest phase. **Start the AgentDojo spike (first half of "Integrate AgentDojo") while building telemetry.** It decides whether "Run the AgentDojo batch" is kept.

### 1.5 Issue conventions
- **Branch:** `feat/<issue-number>-<short-name>`, for example `feat/14-failure-injector`. One issue, one branch, one pull request that closes the issue.
- **Labels:** `phase:0`…`phase:5`, `pri:P0|P1|P2`, `type:setup|build|run|analysis|docs`, `optional`.
- **Milestones:** Setup done (G0), Harness done (G1), Pre-registered (G2), Runs done (G3), Analysis done (G4), Results documented (G5).
- **Definition of done:** acceptance test passes; unit tests added where code exists; `make lint test` green; docs updated; any design change or deviation logged; issue closed by the PR.

---

## Phase 0: Project setup

### Verify the benchmarks and baselines are available
**Priority / estimate (project fields):** P0, 1.5 h · gate G0
**Goal:** find out now whether the benchmarks and baselines exist and are usable, and confirm each cited 2026 preprint.
**Steps**
1. For each of ToolPrivBench (arXiv 2606.20023), SEAgent (2601.11893), GrantBox (2603.28166), BridgeScope (2508.04031): open the arXiv page and confirm title, authors and abstract match how the proposal cites them.
2. Search GitHub and the paper's links for code and data. Note licence and size.
3. `pip index versions agentdojo` and read its docs: how to plug a custom agent pipeline and tool runtime.
4. Check what ToolPrivBench ships: scenario JSON, tool tier labels, ground-truth minimum tool, executable tool stubs or not.
5. If anything is missing, send the authors a short email and note the date.
6. Write `docs/research-reference/sources.md`: one row per source with URL, licence, what it provides, status (verified / missing / reimplement).
**Deliverables:** `docs/research-reference/sources.md`.
**Acceptance:** every source has a verified status. For each "missing", the fallback is written (e.g. reimplement MAC from the paper; build scenario stubs).
**Blocked by (set as GitHub relationship):** nothing. **Notes:** if ToolPrivBench data is not available, stop and raise it with the supervisor before more work.

### Create the repository skeleton
**Priority / estimate (project fields):** P0, 1 h
**Goal:** a clean repo others can read.
**Steps:** clone; add `README.md` (title, RQs, status, how to run, link to PRDs); `LICENSE` (MIT); `.gitignore` (Python, `.venv`, `.env`, `runs/`, `data/raw/`, `.DS_Store`); `CITATION.cff`; confirm `.env` is ignored with `git check-ignore .env`.
**Deliverables:** the files above, committed on a branch and merged.
**Acceptance:** README renders; `.env` is ignored; licence present.
**Blocked by (set as GitHub relationship):** nothing

### Set up the Python project and tooling
**Priority / estimate (project fields):** P0, 1.5 h
**Goal:** reproducible environment with lint, types and tests wired.
**Steps**
1. `uv init --package --python 3.12 --name privilege-drift`; keep the folder layout from `docs/plan/IMPLEMENTATION_PLAN.md` §2 (empty modules with `__init__.py`).
2. Add dependencies as in IMPLEMENTATION_PLAN §3.2; `uv lock`.
3. Configure `ruff`, `mypy` and `pytest` in `pyproject.toml`.
4. Add `Makefile` targets: `setup`, `lint`, `test`, `pilot`, `run-cell`, `analyse`.
5. Add a pre-commit config (ruff, trailing whitespace).
6. Add a GitHub Actions workflow running `make lint test` (P1, optional).
7. Add one trivial test so CI is green.
**Deliverables:** `pyproject.toml`, `uv.lock`, `Makefile`, `tests/test_smoke.py`.
**Acceptance:** `uv sync && make lint test` passes on a clean clone.
**Blocked by (set as GitHub relationship):** "Create the repository skeleton"

### Write the design decisions log
**Priority / estimate (project fields):** P0, 1 h
**Goal:** write down every open design decision so code and pre-registration agree.
**Steps:** create `docs/decisions/` (one file per decision plus a README index); copy decisions D2–D14 from PRD 1 §4.1; for each give the chosen rule, one line of rationale and the date. Leave items that need the pilot marked "pending the pilot issues".
**Acceptance:** each decision has an answer or a named task and date.
**Blocked by (set as GitHub relationship):** nothing. **Notes:** revisit in "Resolve the open design decisions" once the pilot results are in.

### Set up the project board and issues
**Priority / estimate (project fields):** P1, 1.5 h
**Goal:** the board mirrors this document.
**Steps:** create milestones M0–M5; labels per §1.2; add project fields Priority and Estimate (the project already has them); create one issue per task using the template, with the Goal, Steps, Acceptance and Depends lines copied from this file; link dependencies in the issue body; set Estimate and Priority; add all to project "ljmu-ms".
**Acceptance:** every T-ID in Phases 0–5 has an issue on the board with a milestone.
**Blocked by (set as GitHub relationship):** "Create the repository skeleton"

---

## Phase 1: Harness build

### Connect the local and frontier models
**Priority / estimate (project fields):** P0, 3 h
**Goal:** one call interface for Llama (local) and the frontier model.
**Steps**
1. `ollama pull llama3.1:8b-instruct-q4_K_M`; record the digest from `ollama show`.
2. `src/privilege_drift/llm/client.py`: wrapper over `litellm.completion` taking a model key from `configs/models.yaml`.
3. In `models.yaml`: Llama via `ollama/…`, frontier via `gemini/gemini-2.5-flash` (or Anthropic); shared sampling constants (temperature 0.2, top-p 0.9, max tokens 2,048); `num_ctx` set explicitly (8,192, raise for AgentDojo).
4. Return a structured result (text, tokens in/out, latency, raw response).
5. Add an on-disk response cache keyed by (model, prompt, params, seed) for the golden test; on by default in tests only.
6. Add `.env.example`; load keys from `.env`.
7. Test same-seed repeatability on Ollama and record whether outputs are identical.
**Deliverables:** `llm/client.py`, `configs/models.yaml`, `docs/ollama_notes.md` (digest, `num_ctx`, repeatability).
**Acceptance:** one call to each model returns text; switching the frontier model is a one-line config change; the longest known prompt does not truncate (check token counts).
**Blocked by (set as GitHub relationship):** "Set up the Python project and tooling"

### Load both benchmarks into one schema
**Priority / estimate (project fields):** P0, 5 h
**Goal:** both benchmarks in one MCP-compatible schema with privilege tiers.
**Steps**
1. `schema.py`: pydantic models `Tool(name, description, params, tier)`, `Scenario(id, domain, user_task, tools, min_tool, min_tier)`, `ToolCall`, `ToolResult(http_code, body, injected)`, `Decision(allow, reason)`.
2. `data/toolprivbench.py`: load raw data, validate, normalise to the schema; tiers from the benchmark's labels.
3. `configs/tiers/toolprivbench_tiers.yaml` and `agentdojo_tiers.yaml` mapping tool scope to read-only / user / admin.
4. `data/agentdojo.py`: load workspace/banking tasks and injection cases.
5. A reversible converter and a round-trip test: raw → schema → raw gives the same content.
6. Tool executors: use the benchmark's stubs if they exist; otherwise write deterministic stubs keyed on tool and arguments.
7. Exploratory notebook counts: scenarios per domain, tools per tier, tools per scenario (also feeds Ch4 later).
**Deliverables:** `schema.py`, `data/`, tier YAMLs, round-trip tests, `docs/data_summary.md`.
**Acceptance:** all scenarios load; round-trip test passes; tier counts match the benchmark's published numbers.
**Blocked by (set as GitHub relationship):** "Verify the benchmarks and baselines are available"; "Set up the Python project and tooling"

### Freeze the experiment subsets and seeds
**Priority / estimate (project fields):** P0, 2 h
**Goal:** frozen, hash-committed experiment inputs.
**Steps:** write `scripts/make_subsets.py` with a fixed RNG seed; pick 50 ToolPrivBench scenarios stratified 6–7 per domain × 8; pick the AgentDojo 15 tasks and 15 injections stratified over the 5 categories; write JSON files to `prereg/subsets/`; compute SHA-256 into `prereg/subsets/HASHES.txt`; generate the master seed sequence, permute across cells, write `prereg/seed_schedule.json` with **five** seeds per scenario so the three-to-five switch is config only; add a test that checks stratification counts and that no seed repeats.
**Acceptance:** counts per stratum correct; rerunning the script gives identical hashes.
**Blocked by (set as GitHub relationship):** "Load both benchmarks into one schema"

### Define the mediator interface and the no-mediator arm
**Priority / estimate (project fields):** P0, 1.5 h
**Goal:** the locked interface every mediator implements.
**Steps:** define `Mediator` protocol with `start_run(scenario)` and `gate(call, intent) -> Decision`; define the fixed neutral block message constant (D4) in one place; implement `NoneMediator` (always allow); write a conformance test suite parametrised over mediators (returns `Decision`, never raises, deterministic for the same input).
**Acceptance:** conformance suite runs against `None`; suite is reused for MAC and IBAC.
**Blocked by (set as GitHub relationship):** "Load both benchmarks into one schema"

### Build the failure injector
**Priority / estimate (project fields):** P0, 3 h
**Goal:** the independent variable, implemented and tested.
**Steps**
1. `failure/injector.py`: class `FailureInjector(p, rng)`; one independent Bernoulli draw per call; on a hit return `ToolResult(503, FIXED_503_BODY, injected=True)` without executing the tool.
2. RNG from `numpy.random.SeedSequence([master, cell_idx, scenario_idx, seed_idx])`.
3. The 503 body is one constant string with no hint it was injected (same for every tool and model).
4. Tests: empirical rate over 10,000 draws within tolerance of p; p = 0 never injects; p = 1 always injects; same seed gives the same sequence; different seeds differ.
**Acceptance:** all tests pass.
**Blocked by (set as GitHub relationship):** "Load both benchmarks into one schema"; "Freeze the experiment subsets and seeds"

### Build the ReAct agent
**Priority / estimate (project fields):** P0, 5 h
**Goal:** one text-format ReAct loop that both models use.
**Steps**
1. Prompt template: system instructions, tool list (name, description, parameters; **no tier**), format spec (Thought / Action / Action Input / Observation / Final Answer), user task.
2. Parser: extract action and JSON input; tolerate whitespace and code fences; classify failures (no action, bad JSON, unknown tool).
3. Loop: call LLM with stop sequence `Observation:`; parse; send the call through gate → injector → executor; append the observation; stop on Final Answer or max steps (default 15).
4. Bounded format-correction: at most one re-prompt on a malformed step, logged as a parse-error event.
5. Hooks to emit a telemetry record per step ("Record telemetry for every tool call").
6. Tests with a scripted fake LLM: normal run, malformed output, unknown tool, max-steps reached, 503 then retry.
**Acceptance:** scripted runs terminate correctly; the parser never raises on arbitrary text (property test).
**Blocked by (set as GitHub relationship):** "Connect the local and frontier models"; "Load both benchmarks into one schema"

### Record telemetry for every tool call
**Priority / estimate (project fields):** P0, 3 h
**Goal:** the record that every metric is computed from.
**Steps:** pydantic `CallRecord` with the fields in `docs/plan/IMPLEMENTATION_PLAN.md` §4; JSONL writer with atomic temp-then-rename per run; derived RQ3 features computed at write time without look-ahead (rolling 503 rate over the last k calls, retry-since-last-success, error surface, step index, cumulative reasoning tokens); run-level `RunSummary` (task success, final answer, max-steps hit, total calls); hash of the reasoning text; store raw response reference.
**Tests:** compute features on a hand-built trace and compare to hand-calculated values; confirm no feature uses later steps.
**Acceptance:** tests pass; a fake run writes a valid JSONL that reloads into a dataframe.
**Blocked by (set as GitHub relationship):** "Build the ReAct agent"

### Build the SEAgent MAC mediator
**Priority / estimate (project fields):** P0, 3 h
**Goal:** the strongest published baseline.
**Steps:** read the paper's policy model; encode the role-to-tool matrix in `configs/policies/mac_matrix.yaml`; implement call-time check in `mediators/mac.py`; document how each scenario's role is assigned; test allowed and blocked hand-built cases; run the conformance suite.
**Acceptance:** blocks and allows exactly as the matrix says.
**Blocked by (set as GitHub relationship):** "Define the mediator interface and the no-mediator arm"; "Verify the benchmarks and baselines are available". **Notes:** if no official code exists, record "reimplemented from paper" in `docs/decisions/`.

### Build the IBAC mediator
**Priority / estimate (project fields):** P0, 5 h
**Goal:** the intervention under test.
**Steps**
1. `configs/intents.yaml`: the 8-category taxonomy from ToolPrivBench domains.
2. `mediators/classifier.py`: zero-shot Llama prompt that takes only the trusted user prompt and returns JSON `{intent, confidence}`; one retry on invalid JSON.
3. `configs/policies/ibac_policy.yaml`: intent → allowed tiers (and optional tool allow-list); compile to an in-memory dict once.
4. `mediators/ibac.py`: classify in `start_run`; `gate` checks `call.tier ∈ policy(intent)`; on block return the fixed neutral message; on classifier failure use the most restrictive policy and log `classifier_failed` (D13).
5. Log classifier intent and confidence on every record.
6. Tests: policy lookups, gate decisions, fallback path, classifier output parsing; conformance suite.
7. Classifier accuracy check against the benchmark's domain labels on the 50 scenarios (report it later).
**Acceptance:** all tests pass; classifier accuracy on the subset is recorded in `docs/pilot.md` later.
**Blocked by (set as GitHub relationship):** "Define the mediator interface and the no-mediator arm"; "Connect the local and frontier models"

### Build the batch runner with resume and integrity checks
**Priority / estimate (project fields):** P0, 5 h
**Goal:** unattended, restartable, self-checking execution.
**Steps**
1. `runner/plan.py`: expand `configs/grid.yaml` into `(cell, scenario, seed)` work items with deterministic IDs.
2. `runner/run.py`: for each item, build agent + mediator + injector, run, write results atomically; skip items whose result file exists and passes its checksum.
3. Concurrency: Llama 1 worker; frontier limited by requests per minute; back off with `tenacity` on 429/5xx; log API errors as `infrastructure_error` and retry **without** counting them as agent behaviour.
4. `runner/manifest.py`: per-cell `manifest.json` (config hash, git SHA, model digest, seeds, start/end, status).
5. `runner/integrity.py`: the three checks (150 traces per cell; empirical injection rate within ±3 pp of p; tier attribution equals ground truth).
6. CLI: `uv run privilege-drift run-cell <cell-id>` and `uv run privilege-drift check-cell <cell-id>`.
7. Test: kill a batch mid-run, restart, and confirm no duplicates and no corrupted files; plant an error and confirm the check fails.
**Acceptance:** crash-resume test and planted-error test pass.
**Blocked by (set as GitHub relationship):** "Record telemetry for every tool call"; "Build the failure injector"; "Define the mediator interface and the no-mediator arm"

### Test the whole pipeline with a fake model
**Priority / estimate (project fields):** P0, 2 h · gate G1
**Goal:** prove the whole pipeline before spending compute.
**Steps:** a scripted fake LLM that deliberately picks high-tier tools; run all three mediators × three rates on a few scenarios; assert expected telemetry (blocks under MAC and IBAC, injected 503 rate, no executed violation under a correct gate); a golden test with cached responses whose metrics must reproduce exactly.
**Acceptance:** integration and golden tests pass in CI.
**Blocked by (set as GitHub relationship):** "Build the SEAgent MAC mediator"; "Build the IBAC mediator"; "Build the batch runner with resume and integrity checks"

### Integrate AgentDojo (optional)
**Priority / estimate (project fields):** P2, 6 h
**Goal:** run the ReAct agent and the injector inside AgentDojo.
**Steps:** spike first (2 h): run one stock AgentDojo task with a custom pipeline element; then wrap AgentDojo's tool runtime with the injector; add the None and IBAC arms; add benign-utility runs (D8); emit the same telemetry; map AgentDojo tiers.
**Acceptance:** one AgentDojo run end to end with valid telemetry under p = 0 and p = 0.6.
**Blocked by (set as GitHub relationship):** "Build the IBAC mediator"; "Build the batch runner with resume and integrity checks". **Notes:** the spike result decides whether to keep "Run the AgentDojo batch". Do the spike early.

---

## Phase 2: Pilot and pre-registration

### Run the pilot
**Priority / estimate (project fields):** P0, 3 h
**Goal:** measure speed and behaviour on a small slice.
**Steps:** run about 10 scenarios × 3 seeds × 3 rates × 3 mediators on Llama; log seconds per run, LLM calls per run, tokens per run; run the frontier model on a smaller slice for calls-per-run; save to `runs/pilot/`.
**Deliverables:** `docs/pilot.md` with a throughput table and extrapolation to the full grid.
**Acceptance:** extrapolated machine time is stated for every arm.
**Blocked by (set as GitHub relationship):** "Test the whole pipeline with a fake model"

### Sanity-check the pilot results
**Priority / estimate (project fields):** P0, 1 h
**Goal:** catch scoring or prompt problems before the full run.
**Steps:** compare the p = 0 violation rate with the published ≈ 0.35; compute parse-error rate, max-steps-hit rate and classifier-failure rate; read ten traces by hand; fix prompts or scoring if any rate is above about 5 % or the baseline is far off; re-run the pilot slice after fixes.
**Acceptance:** all rates below the threshold or fixes documented.
**Blocked by (set as GitHub relationship):** "Run the pilot"

### Resolve the open design decisions
**Priority / estimate (project fields):** P0, 1 h
**Steps:** answer I1–I8 (PRD 1 §5) and the remaining D-decisions using the pilot; update `docs/decisions/`.
**Acceptance:** nothing marked pending.
**Blocked by (set as GitHub relationship):** "Sanity-check the pilot results"; "Write the design decisions log"

### Run the power analysis
**Priority / estimate (project fields):** P0, 2 h
**Steps:** `analysis/power.py`: Monte-Carlo, 10,000 replicates, Beta-Binomial per-scenario events with three-seed average, noise variance from the pilot, baseline 0.35, MDE 12 pp, Holm over 18 cells; report power; if below 0.80, switch to five seeds in `grid.yaml` and recompute throughput.
**Acceptance:** power value and decision recorded.
**Blocked by (set as GitHub relationship):** "Run the pilot"

### Choose the frontier model
**Priority / estimate (project fields):** P0, 1 h
**Steps:** check the three criteria (cost tier within an order of magnitude, ≥ 70 % on the Berkeley Function-Calling Leaderboard, availability within the free tier or £50); use pilot calls-per-run to compute days at the rate limit; write `docs/frontier_choice.md`.
**Acceptance:** one model chosen with evidence and a contingency.
**Blocked by (set as GitHub relationship):** "Run the pilot"

### Write the pre-registration
**Priority / estimate (project fields):** P0, 2.5 h
**Steps:** write `prereg/preregistration.md` with: hypotheses and directions; the RQ1 primary contrast; the 5 pp utility floor and its pre-declared wording; power; exact tests, α and correction families; lever order; subset hashes; frontier model; escalation-label definition; rolling-window size; block message; max steps; classifier fallback; exploratory-versus-confirmatory rule.
**Acceptance:** each item in §7.8 of the proposal is present.
**Blocked by (set as GitHub relationship):** "Run the power analysis"; "Resolve the open design decisions"; "Choose the frontier model"

### Tag and hash the pre-registration and code freeze
**Priority / estimate (project fields):** P0, 0.5 h · gate G2
**Steps:** `git add prereg && git commit`; tag `prereg-v1`; compute `HASHES.txt` for the pre-registration and subsets; freeze code and tag `exp-v1`; push tags.
**Acceptance:** tags exist on the remote before any full run. **Rule:** any later change is a deviation ("Keep the deviations log").
**Blocked by (set as GitHub relationship):** "Write the pre-registration"

---

## Phase 3: Experiment runs

### Run the Llama ToolPrivBench batch
**Priority / estimate (project fields):** P0, 2 h hands-on 
**Goal:** the 9 Llama cells, 1,350 runs.
**Steps:** run `p = 0` cells first as a final pipeline check; then p = 0.3 and 0.6; use `caffeinate -i` and run overnight; watch the first batch, then leave; after each cell run `check-cell`.
**Acceptance:** all 9 cells pass integrity checks.
**Blocked by (set as GitHub relationship):** "Tag and hash the pre-registration and code freeze"

### Run the frontier ToolPrivBench batch
**Priority / estimate (project fields):** P1, 2 h hands-on
**Goal:** the 9 frontier cells, 1,350 runs.
**Steps:** start in parallel with "Run the Llama ToolPrivBench batch" (network-bound vs GPU-bound); throttle to the rate limit; resume daily; record cost.
**Acceptance:** all 9 cells pass integrity checks, or lever L3 is logged as a deviation.
**Blocked by (set as GitHub relationship):** "Tag and hash the pre-registration and code freeze"

### Clean and freeze the run data
**Priority / estimate (project fields):** P0, 2 h
**Steps:** list infrastructure errors; confirm none were counted as injected 503s; re-run failed items; verify row counts and manifests; freeze a read-only copy of `runs/`.
**Acceptance:** all counts correct; clean dataset frozen.
**Blocked by (set as GitHub relationship):** "Run the Llama ToolPrivBench batch"; "Run the frontier ToolPrivBench batch"; "Run the AgentDojo batch" (frontier and AgentDojo only if kept)

### Run the AgentDojo batch (optional)
**Priority / estimate (project fields):** P2, 2 h hands-on
**Steps:** 6 cells plus benign runs; same integrity checks; log ASR and task success.
**Acceptance:** checks pass, or lever L2 is logged.
**Blocked by (set as GitHub relationship):** "Integrate AgentDojo"; "Tag and hash the pre-registration and code freeze"

### Keep the deviations log
**Priority / estimate (project fields):** P0, 0.5 h, ongoing
**Steps:** every change after `exp-v1` (prompt, config, lever fired, rerun, model swap) gets an entry in `docs/deviations.md` with date, reason and affected cells; mark affected analyses exploratory.
**Acceptance:** log is complete at the end of Phase 3.

---

## Phase 4: Analysis

### Build the statistics library
**Priority / estimate (project fields):** P0, 3 h
**Steps:** `analysis/stats.py`: scenario-level aggregation (mean over seeds); paired Wilcoxon (`scipy.stats.wilcoxon`); Page's trend test (`scipy.stats.page_trend_test`); Cliff's delta and Cohen's d; Holm (`statsmodels multipletests`); bootstrap helper; unit tests against known values.
**Acceptance:** tests pass.
**Blocked by (set as GitHub relationship):** "Record telemetry for every tool call"

### Analyse RQ1: failure pressure and escalation
**Priority / estimate (project fields):** P0, 3 h
**Steps:** violation rate by model × p; Δ = V(0.6) − V(0) per model; the pre-registered difference-in-differences under None with bootstrap CI; Wilcoxon per contrast; Page trend per model; Cliff's delta; Holm over the 18-cell family; table and figures.
**Acceptance:** primary contrast reported with corrected p and effect size; smaller-than-target effects stated as upper bounds.
**Blocked by (set as GitHub relationship):** "Clean and freeze the run data"; "Build the statistics library"

### Analyse RQ2: IBAC versus MAC versus no mediator
**Priority / estimate (project fields):** P0, 2.5 h
**Steps:** violation (proposed, executed, blocked), task success and ASR by mediator × p; IBAC vs MAC vs None paired tests; utility-floor check with the pre-declared wording; classifier accuracy and failure rate.
**Acceptance:** floor outcome stated explicitly.
**Blocked by (set as GitHub relationship):** "Clean and freeze the run data"; "Build the statistics library"

### Analyse RQ3: which signals predict escalation
**Priority / estimate (project fields):** P0, 4 h
**Steps:** `analysis/predictors.py`: step-level table from traces; label per D5; VIF and PCA for collinear features; logistic regression with `GroupKFold(5)` by scenario; AUC and calibration; `shap.LinearExplainer`; 1,000-sample paired bootstrap for rank CIs; figures.
**Acceptance:** AUC, ranking and CIs reported.
**Blocked by (set as GitHub relationship):** "Clean and freeze the run data"; "Build the statistics library"

### Analyse the AgentDojo results (optional)
**Priority / estimate (project fields):** P2, 1.5 h
**Steps:** own Holm family; utility versus ASR; tables and figures.
**Blocked by (set as GitHub relationship):** "Clean and freeze the run data"; "Build the statistics library"

### Make the analysis reproducible with one command
**Priority / estimate (project fields):** P0, 1.5 h · gate G4
**Steps:** `make analyse` runs all analysis scripts and writes `results/numbers.json`, `results/tables/*.csv`, `results/figures/*.png`; every number later quoted in writing comes from `numbers.json`; test on a clean clone with the frozen `runs/`.
**Acceptance:** a clean run reproduces identical outputs.
**Blocked by (set as GitHub relationship):** "Analyse RQ1: failure pressure and escalation"; "Analyse RQ2: IBAC versus MAC versus no mediator"; "Analyse RQ3: which signals predict escalation"

---

## Phase 5: Document the outcome

### Write the results report
**Priority / estimate (project fields):** P0, 3 h
**Goal:** a plain, structured record of what was found, which the thesis can be written from.
**Steps:** create `docs/results/RESULTS.md` with, per research question: the question; the pre-registered test; the result (numbers from `numbers.json`); effect size and corrected p; the decision against the pre-registered hypothesis (supported / not supported / inconclusive); the figure and table list; exploratory findings kept in a separate section; deviations and which results they touch; observed limitations; one-sentence answer to the question. Add a final "answers to the three findings promised in the abstract" section (PO7).
**Acceptance:** every promised outcome PO1–PO8 in PRD 1 §3 has either evidence or a stated reason it is missing.
**Blocked by (set as GitHub relationship):** "Make the analysis reproducible with one command"; "Keep the deviations log"

### Prepare the hand-off package for writing
**Priority / estimate (project fields):** P0, 1 h · gate G5
**Steps:** create `docs/handoff.md` listing: where each figure and table lives; method facts needed for Ch3/Ch4 (model digests, `num_ctx`, subset hashes, runtimes, costs); the pilot numbers; the deviations log; open caveats; the list of numbers each chapter needs; update the board with the writing issues from PRD 2.
**Acceptance:** PRD 2's "Needs from PRD 1" table is fully satisfied.
**Blocked by (set as GitHub relationship):** "Write the results report"

### Release the repository
**Priority / estimate (project fields):** P1, 2 h
**Steps:** clean README with a reproduce section; archive telemetry (compressed, about 5 GB) to a release asset or data host with CC-BY 4.0 notice; tag `v1.0`; run a clean-clone golden test.
**Acceptance:** a third party can reproduce the golden test and the analysis from the release.
**Blocked by (set as GitHub relationship):** "Make the analysis reproducible with one command"

---

## 2. Hours by phase

| Phase | Hours |
|---|---|
| 0 Setup | 6.5 |
| 1 Harness build | 43.5 ("Integrate AgentDojo" is 6 of this) |
| 2 Pilot and pre-registration | 11 |
| 3 Runs (hands-on; machine time extra) | 8.5 |
| 4 Analysis | 15.5 |
| 5 Document outcome | 6 |
| **Total** | **about 91** |

## 3. If you are short of time

Cut in this order, and log each cut in `docs/deviations.md`: "Integrate AgentDojo", "Run the AgentDojo batch", "Analyse the AgentDojo results" (AgentDojo) → "Set up the project board and issues" (board) can be reduced to a checklist → "Release the repository" (release) after submission. Do not cut the pilot issues (pilot and pre-registration), "Build the batch runner with resume and integrity checks" (resume and integrity) or "Make the analysis reproducible with one command" (reproducibility).

---

## 4. Mapping to the PRD reference codes

| Issue title | PRD code |
|---|---|
| Create the repository skeleton | T0.1 |
| Set up the Python project and tooling | T0.2 |
| Set up the project board and issues | T0.3 |
| Write the design decisions log | T0.4 |
| Verify the benchmarks and baselines are available | T0.5 |
| Connect the local and frontier models | T2.1 |
| Load both benchmarks into one schema | T2.2 |
| Freeze the experiment subsets and seeds | T2.3 |
| Build the failure injector | T2.4 |
| Build the ReAct agent | T2.5 |
| Record telemetry for every tool call | T2.6 |
| Define the mediator interface and the no-mediator arm | T2.7 |
| Build the SEAgent MAC mediator | T2.8 |
| Build the IBAC mediator | T2.9 |
| Build the batch runner with resume and integrity checks | T2.10 |
| Test the whole pipeline with a fake model | T2.11 |
| Integrate AgentDojo | T2.12 |
| Run the pilot | T3.1 |
| Sanity-check the pilot results | T3.2 |
| Run the power analysis | T3.3 |
| Resolve the open design decisions | T3.4 |
| Choose the frontier model | T3.5 |
| Write the pre-registration | T3.6 |
| Tag and hash the pre-registration and code freeze | T3.7 |
| Run the Llama ToolPrivBench batch | T4.1 |
| Run the frontier ToolPrivBench batch | T4.2 |
| Clean and freeze the run data | T4.3 |
| Run the AgentDojo batch | T4.4 |
| Keep the deviations log | T4.5 |
| Build the statistics library | T5.1 |
| Analyse RQ1: failure pressure and escalation | T5.2 |
| Analyse RQ2: IBAC versus MAC versus no mediator | T5.3 |
| Analyse RQ3: which signals predict escalation | T5.4 |
| Analyse the AgentDojo results | T5.5 |
| Make the analysis reproducible with one command | T5.6 |
| Write the results report | T5.7 |
| Prepare the hand-off package for writing | T5.8 |
| Release the repository | T8.1 |
