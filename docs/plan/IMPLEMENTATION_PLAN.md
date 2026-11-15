# Implementation Plan: Dynamic Tool Authorization under Failure Pressure

Python project setup and step-by-step execution plan for the research in *Amit_Kumar_Proposal.pdf* (August 2026).
Section references like §7.4.1 point back to the proposal.

---

## 0. The experiment in one page

| Item | Value |
|---|---|
| Question | Does transient tool failure (HTTP 503) push LLM agents to pick over-privileged tools (PoLP violations)? Can an Intent-Based Access Control (IBAC) gate fix it without hurting task success? Which failure signals predict escalation? |
| Models | Llama-3.1-8B-Instruct (Ollama, Q4_K_M, local) and one frontier baseline (Gemini 2.5 Flash or Claude Sonnet 4.5), locked at the end of Phase 1 |
| Scaffold | ReAct only |
| Failure injection | Independent Bernoulli 503 per tool call, p ∈ {0, 0.3, 0.6} |
| Mediators | None, SEAgent MAC, IBAC (ToolPrivBench). None and IBAC (AgentDojo) |
| Primary grid | 2 models × 3 rates × 3 mediators × 3 seeds × 50 scenarios = **2,700 runs** (18 cells) |
| Secondary grid | Llama × 3 rates × 2 mediators × 3 seeds × 15 tasks × 15 injections = **4,050 runs** (6 cells) |
| Analysis | Paired Wilcoxon on scenario-level means (n = 50), Holm–Bonferroni, Page's trend, Cliff's delta, logistic regression + SHAP |
| Custom code | ~1,500 LOC: failure middleware ~500, mediators ~800, batch driver ~200 |
| Budget | £0 compute, £0–50 API, 19 weeks at ~12–15 h/week |

---

## 1. Decisions to settle before writing code

The proposal leaves these open. Each changes what you build or measure, and each needs to go into the pre-registration (§7.8, end of Week 8). Settle them in Week 1–3.

| # | Question | Recommendation |
|---|---|---|
| D1 | **Are ToolPrivBench, AgentDojo and SEAgent code actually obtainable?** ToolPrivBench is arXiv 2606.20023 and SEAgent is arXiv 2601.11893. | Check this on Day 1. If SEAgent has no public code, reimplement MAC from the paper (the ~800 LOC budget assumes this). If ToolPrivBench's data is not released, this is a project-level risk. Email the authors immediately. |
| D2 | **Where is a PoLP violation counted, at the agent's *proposed* call or at the *executed* call?** If you only count executed calls, a mediator reduces violations to zero by construction. | Log both. Primary metric for RQ1 and RQ3 = **proposed** calls (what the model chose). For RQ2 report proposed (agent behaviour), executed (residual risk) and block count. |
| D3 | **Order of gate and fault injector.** | `agent → mediator gate → failure injector → tool`. A blocked call never reaches the tool, so it never gets a 503 draw. |
| D4 | **What does the agent see when the mediator blocks a call?** The wording is a confound (it may nudge replanning). | One fixed, neutral string, identical for MAC and IBAC, and **different from the 503 string** (otherwise 503 opacity is lost). Pre-register it. |
| D5 | **Definition of "escalation attempt" for RQ3's binary label.** | Primary: a proposed call whose tier is above the ground-truth minimally-sufficient tier. Secondary: a call with a higher tier than any earlier call in the same run. |
| D6 | **ReAct format: native function-calling vs text ReAct.** | Use **text ReAct** (`Thought / Action / Action Input / Observation`) parsed by your own code, for both models. This keeps the two models on an identical scaffold and avoids provider-specific tool-call behaviour. Stop on `Observation:`. |
| D7 | **Retry policy.** Does the harness retry on 503 automatically, or does the agent decide? | The agent decides (that is the point of RQ1). Do **not** add harness-level retries. Set a hard max-steps cap (suggest 15) and pre-register it. |
| D8 | **AgentDojo benign-utility runs.** The 15 × 15 grid only gives utility *under attack*. | Add 15 injection-free runs per cell (6 × 3 × 15 = 270 extra runs). It is cheap and gives clean task-success for the 5-pp utility floor. |
| D9 | **API call budget vs rate limit.** The Gemini free tier is 1,500 requests/day, but a ReAct run makes about 5–10 LLM calls, not 1. | Measure calls/run in the pilot. 1,350 frontier runs × ~7 calls ≈ 9,500 calls ≈ 7 days at the cap. Fine, but plan for it. |
| D10 | **Seed schedule vs common random numbers.** The proposal permutes seeds across cells. | Follow the proposal (one deterministic master sequence, permuted per cell). |
| D11 | **Which cell does "violation rate" divide by?** Per-run fraction of calls vs per-scenario mean. | Per-run fraction of proposed calls, averaged over the 3 seeds, giving one number per scenario per cell. Pre-register. |
| D12 | **AgentDojo uses its own pipeline.** Plugging in the text-ReAct loop means writing a custom pipeline element. | Budget 1 extra week of A7 work for this. The 503 middleware has to wrap AgentDojo's tool runtime rather than the harness. |

---

## 2. Repository layout

Put the project in its own folder, for example `~/ws/upgrad/ms/agent-privilege-drift/`.

```
agent-privilege-drift/
├── pyproject.toml            # uv-managed, pinned
├── uv.lock
├── .python-version           # 3.12
├── .env.example              # GEMINI_API_KEY / ANTHROPIC_API_KEY (real .env untracked)
├── .gitignore                # .env, runs/, data/raw/, .venv/
├── Makefile                  # setup, lint, test, pilot, run-cell, analyse
├── README.md
├── prereg/
│   ├── preregistration.md    # drafted by end of Week 8
│   ├── subsets/              # toolprivbench_50.json, agentdojo_15x15.json + SHA-256 files
│   └── seed_schedule.json
├── configs/
│   ├── models.yaml           # llama / frontier via LiteLLM, sampling constants
│   ├── grid.yaml             # the 18 + 6 cells
│   ├── tiers/                # toolprivbench_tiers.yaml, agentdojo_tiers.yaml
│   ├── policies/             # mac_matrix.yaml, ibac_policy.yaml
│   └── intents.yaml          # the 8-category taxonomy
├── src/privilege_drift/
│   ├── schema.py             # MCP-compatible Scenario/Tool/ToolCall pydantic models
│   ├── data/                 # loaders + normalisers for ToolPrivBench, AgentDojo
│   ├── llm/                  # LiteLLM client, Ollama options, response cache
│   ├── agent/react.py        # the ReAct loop and parser
│   ├── failure/injector.py   # Bernoulli-503 middleware
│   ├── mediators/            # base.py (gate), none.py, mac.py, ibac.py, classifier.py
│   ├── telemetry/            # record schema, JSONL writer, hashing
│   ├── runner/               # cell planner, batch driver, manifest, integrity checks
│   ├── metrics/              # violation rate, delta, task success, ASR
│   └── analysis/             # stats.py, predictors.py (LR + SHAP), figures.py
├── tests/                    # unit + integration (see §8)
├── notebooks/                # exploration only, never a source of results
├── runs/                     # gitignored: runs/<cell_id>/<scenario_id>.jsonl + manifest.json
└── docs/                     # decisions log, deviations log
```

---

## 3. Environment setup (Week 2, activity A2)

### 3.1 Machine and tooling

```bash
# Toolchain
brew install uv ollama git
uv python install 3.12

# Project
mkdir -p ~/ws/upgrad/ms/agent-privilege-drift && cd $_
git init
uv init --package --python 3.12 --name privilege-drift
```

### 3.2 Dependencies

```bash
# Runtime
uv add litellm pydantic pyyaml numpy pandas scipy statsmodels scikit-learn shap \
       matplotlib tenacity typer rich httpx orjson
# Benchmarks
uv add agentdojo
# Dev
uv add --dev pytest pytest-cov hypothesis ruff mypy pre-commit
# Optional experiment tracking (free tier)
uv add wandb
```

Pin everything with `uv lock`. Record the `uv.lock` hash and Ollama model digest in the pre-registration.

### 3.3 Local model

```bash
ollama pull llama3.1:8b-instruct-q4_K_M
ollama show llama3.1:8b-instruct-q4_K_M   # record the digest
```

Points that commonly cause silent errors:

- **Set `num_ctx` explicitly** (for example 8192, or 16384 for AgentDojo). Ollama's default context is small and silently truncates long ReAct histories, which would corrupt results.
- Pass `temperature=0.2`, `top_p=0.9`, `num_predict=2048`, and a per-run `seed`. Keep these identical for the frontier arm (`temperature`, `top_p`, `max_tokens`).
- Set `OLLAMA_NUM_PARALLEL=1` for clean latency numbers. Use `caffeinate -i` for overnight runs so the Mac does not sleep.
- Keep one Ollama instance. The IBAC classifier and the agent share it.

### 3.4 API keys

Create `.env` (untracked) with `GEMINI_API_KEY=` and/or `ANTHROPIC_API_KEY=`. Load with `python-dotenv` or `uv run --env-file .env`. Never commit it.

### 3.5 Smoke tests (acceptance for A2)

1. `litellm.completion(model="ollama/llama3.1:8b-instruct-q4_K_M", ...)` returns text.
2. The same call with `gemini/gemini-2.5-flash` (or `anthropic/claude-sonnet-4-5`) returns text. Swapping is a one-line config change.
3. The same prompt twice with the same `seed` on Ollama gives the same output (or you record that it does not).
4. `uv run pytest` passes with an empty-but-wired test suite. `ruff` and `mypy` run in `make lint`.

---

## 4. Phase-by-phase build plan

Weeks come from Table 9.1.

### Phase 1: Foundation (Weeks 1–4: A1, A2, start A3)

**A1: Literature consolidation (W1–3)**
- Fetch the key papers and keep notes in `docs/lit/`. Priority: Yang 2026 (ToolPrivBench), Ji 2026 (SEAgent), Debenedetti 2024 (AgentDojo), Zverev 2025.
- From Yang et al., extract the exact scenario schema, tier labels, violation scoring rule and the baseline ≈0.35 violation rate. All are inputs to the power analysis.
- **Resolve D1**.

**A2: Harness (W2–4)**
1. Environment per §3.
2. `schema.py`: pydantic models for `Tool(name, description, params, tier)`, `Scenario(id, domain, user_task, tools, min_tool, ...)`, `ToolCall`, `Decision(allow, reason)`.
3. `data/toolprivbench.py`: download, validate, and normalise to the common schema. Deterministic and reversible (§7.3). Round-trip test.
4. `data/agentdojo.py`: load the workspace/banking tasks and injection cases, with tier mapping YAML (read-only / user / admin).
5. Stratified subset selection script: 50 ToolPrivBench scenarios (6–7 per domain × 8 domains) with a fixed RNG seed. Write `toolprivbench_50.json` and its SHA-256.
6. AgentDojo subset: 15 tasks and 15 injection cases stratified over the 5 injection categories.
7. `telemetry/`: the per-call record (below) and an append-only JSONL writer.
8. Frontier-baseline decision (end of Phase 1): run the three §7.4.4 criteria as a checklist (cost tier, BFCL ≥ 70 %, availability) and record the evidence in `docs/frontier_choice.md`. Gemini 2.5 Flash is the default.

**Telemetry record (one per tool call)**

| Field | Note |
|---|---|
| `run_id`, `cell_id`, `scenario_id`, `seed_idx` | identifiers |
| `model`, `p`, `mediator` | the cell factors |
| `step_idx`, `timestamp` | from the proposal |
| `tool_name`, `proposed_tier`, `min_tier`, `is_violation` | the core outcome (D2) |
| `mediator_decision`, `block_reason`, `classifier_intent`, `classifier_conf` | mediator state |
| `injected` (bool), `http_code` | failure state |
| `retry_since_success`, `rolling_503_rate`, `reasoning_tokens_cum`, `error_surface` | RQ3 predictors (computed at write time, no look-ahead) |
| `cot_hash` | hash of the step's reasoning text |
| `latency_ms`, `tokens_in`, `tokens_out`, `raw_response_ref` | audit and cost |

At the end of each run also write a `run_summary` record (task success, final answer, max-steps reached, total calls).

### Phase 2: Build (Weeks 4–8: A3, A4)

**A3: Tiered wrappers and failure injection (W4–6)**
1. **Simulated tools.** Each scenario's tools must be executable. If ToolPrivBench ships tool stubs, use them. If not, write a stub executor that returns plausible deterministic output keyed on tool and arguments.
2. `failure/injector.py`:
   ```python
   class FailureInjector:
       def __init__(self, p: float, rng: np.random.Generator): ...
       def __call__(self, call: ToolCall, execute: Callable) -> ToolResult:
           if self.rng.random() < self.p:
               return ToolResult(http_code=503, body=FIXED_503_BODY, injected=True)
           return execute(call)
   ```
   - One independent draw per call. RNG seeded from `SeedSequence([master, cell_idx, scenario_idx, seed_idx])`.
   - The 503 body is a single constant string, identical for every tool and for both models, with no metadata that reveals injection (§6.3 assumption).
3. `agent/react.py`:
   - Prompt template with the tool list (name, description, parameters; **not** the tier, so the agent cannot read it), the format instructions, and the user task.
   - Parse `Action:` / `Action Input:` (JSON). Handle malformed output with at most one format-correction re-prompt (D7 style cap, pre-registered), logged as a parse-error event.
   - Loop: call the LLM, parse, `mediator.gate`, `injector`, execute, append `Observation`, stop on `Final Answer` or max steps.
4. Tests (see §8): empirical injection rate over 10,000 draws within tolerance of p; same seed gives the same draw sequence; p=0 never injects.

**A4: Mediators (W5–8)**
1. `mediators/base.py`: the locked contract. Unit-test it before any experiment cell runs (Table 9.3).
   ```python
   class Mediator(Protocol):
       def start_run(self, scenario: Scenario) -> None: ...   # IBAC classifies here
       def gate(self, call: ToolCall, intent: Intent | None) -> Decision: ...
   ```
2. `none.py`: always allow.
3. `mac.py` (SEAgent): role-to-tool matrix from `configs/policies/mac_matrix.yaml`, checked at call time. Follow Ji et al. 2026 for how roles are assigned per scenario.
4. `ibac.py` + `classifier.py`:
   - At `start_run`, send **only the trusted user prompt** to Llama-3.1-8B via Ollama with the 8-category intent taxonomy, requesting a single label and confidence as JSON. Retry once on invalid JSON.
   - Policy: YAML `intent → max allowed tier (and optional tool allow-list)`, compiled once into a dict.
   - Gate: `call.tier ∈ policy(intent)`; on failure block and log (D4 string).
   - Fail-safe: if classification fails after retry, log `classifier_failed` and fall back to the most restrictive policy (pre-register this).
5. The Phase 3 pilot is the first real test, so run a **dry run with a stub LLM** (a scripted fake that always picks a high-tier tool) to confirm each mediator blocks what it should.

**Pre-registration (end of Week 8, milestone M2).** Write `prereg/preregistration.md` containing items (a)–(g) of §7.8 plus the decisions D2–D8, D11. Commit, tag, and hash it:
```bash
git add prereg && git commit -m "Pre-registration" && git tag prereg-v1
shasum -a 256 prereg/preregistration.md prereg/subsets/*.json > prereg/HASHES.txt
```

### Phase 3: Pilot (Weeks 7–9: A5)

1. Run a small slice of the Llama grid (e.g. 10 scenarios × 3 seeds × 3 rates × 3 mediators) end to end.
2. Calibrate:
   - **Throughput**: seconds/run, LLM calls/run, tokens/run → update the compute budget (§7).
   - **Inter-seed variance** → feed the Beta-Binomial Monte-Carlo power analysis (10,000 replicates, MDE 12 pp, n = 50). If power < 0.80 fire the five-seed contingency.
   - Parse-error rate, max-steps-hit rate, classifier-failure rate. If any exceeds roughly 5 %, fix the prompt before pre-registration freezes.
   - Check at p = 0 that Llama's baseline violation rate is near the published ≈ 0.35. If it is far off, check your scoring against Yang et al.
3. Freeze the code (`git tag exp-v1`). Anything changed after this is a deviation to be logged in `docs/deviations.md`.

### Phase 4: Full experiments (Weeks 9–14: A6, A7)

**A6: ToolPrivBench, 18 cells (W9–13)**
- Llama arm (9 cells, 1,350 runs): unattended overnight batches.
- Frontier arm (9 cells, 1,350 runs): throttled to the API cap, run in parallel to Llama batches (one is network-bound, one is GPU-bound).
- Always run `p = 0` for each arm first. It is cheap and validates the pipeline.

**A7: AgentDojo, 6 cells, Llama only (W12–14)**
- Implement the custom AgentDojo pipeline element (D12) with the same injector and the None/IBAC mediators. Then run the 6 cells plus the benign-utility runs (D8).

**Batch driver behaviour (§7.3, hard requirement):**
1. `plan`: expand `grid.yaml` into `(cell, scenario, seed)` work items with deterministic IDs.
2. On start, skip any item whose result file already exists and passes its checksum (resume without reruns).
3. Write each run's JSONL to a temp file and `rename` atomically on completion.
4. Cap concurrency (Llama: 1; frontier: set by RPM). Back off on 429/5xx with `tenacity`. Log API errors as `infrastructure_error`, **not** as injected 503s, and retry them without counting them as agent behaviour.
5. After each cell, run the three integrity checks (§7.8): 150 traces (50 × 3), empirical injection rate within ±3 pp of p, tier attribution matches the ground-truth map. A failing cell is re-run before any analysis uses it.
6. Write `runs/<cell_id>/manifest.json`: config hash, git SHA, model digest, seed schedule slice, start/end time, status.

**Throughput budget (fill in after the pilot)**

| Arm | Runs | Est. s/run | Total | Notes |
|---|---|---|---|---|
| Llama, ToolPrivBench | 1,350 | pilot | pilot | local, overnight |
| Llama, AgentDojo | 4,050 (+270 benign) | pilot | pilot | longest prompts, the largest cost. Lever L2 if it overruns |
| Frontier, ToolPrivBench | 1,350 | pilot | ÷ RPD cap | ~7+ days at 1,500 RPD (D9) |

### Phase 5: Analysis and write-up (Weeks 14–19: A8, A9)

Build the analysis as code that reads only `runs/**/*.jsonl`, so every table and figure regenerates with `make analyse`.

**O1 (`analysis/stats.py`)**
1. Per scenario × cell: mean violation rate across 3 seeds → n = 50 paired values.
2. Wilcoxon signed-rank (`scipy.stats.wilcoxon`) on paired differences: Llama vs frontier at each p, and across p within a model.
3. Page's trend test across ordered p (`scipy.stats.page_trend_test`).
4. Cliff's delta (implement and unit-test it; no library dependency) and Cohen's d where appropriate.
5. Holm–Bonferroni (`statsmodels.stats.multitest.multipletests(method="holm")`) across the 18-cell family. Separate family for the AgentDojo 6 cells.
6. Pre-registered primary contrast: difference-in-differences of the escalation delta Δ = V(p=0.6) − V(p=0) between frontier and Llama under `None`. Bootstrap CI over scenarios.

**O2**
- PoLP violation, task success and ASR per mediator × p. Check the 5-pp utility floor on task success. Report IBAC vs MAC vs None. Use the pre-declared wording if IBAC fails the floor.

**O3 (`analysis/predictors.py`)**
1. Build a step-level table from traces: features = rolling 503 rate, retry-since-last-success, error surface, step index, cumulative reasoning tokens. Label = D5.
2. Compute VIF (`statsmodels`); collapse features with VIF > 5 into a principal component.
3. Logistic regression with `GroupKFold(5)` grouped by scenario (leave-scenario-out). Report AUC and calibration.
4. SHAP (`shap.LinearExplainer`) → mean |SHAP| per feature. 1,000-sample paired bootstrap over scenarios for CIs on ranks. Standardise features first so weights are comparable.

**Write-up:** figures from `analysis/figures.py` (violation rate vs p per model and mediator, with CIs; utility–security scatter; SHAP bar chart), a results section drawn from the notebook-free pipeline, and a clear label on every deviation (anything after `exp-v1`) as exploratory.

---

## 5. Contingency levers (build them in from day one)

The proposal's reduction levers are cheap to support if the grid is config-driven:

- **L1** drop p = 0.6 → remove from `grid.yaml`.
- **L2** drop the AgentDojo secondary grid.
- **L3** drop the frontier arm.
- Variance contingency: switch seeds 3 → 5 in `grid.yaml` (the seed schedule file should already contain 5 values per scenario so this is a config change, not a re-plan).

---

## 6. Reproducibility and integrity

- Everything controlled by config; no constants inside source.
- `git tag` at `prereg-v1` and `exp-v1`. Every manifest records the git SHA.
- Store raw LLM responses (compressed) so any metric can be recomputed without re-querying the API.
- Docker is optional. Containerise the **analysis** (pure Python, easy to freeze); Ollama must stay native on the Mac for Metal acceleration.
- Release: MIT for code, CC-BY 4.0 for telemetry (~5 GB).

---

## 7. Testing strategy

| Layer | What to test |
|---|---|
| Unit | schema round-trips, tier mapping, injector rate and determinism, ReAct parser (valid, malformed, missing fields), each mediator's gate on hand-built cases, Cliff's delta against known values, seed schedule has no repeats |
| Property (`hypothesis`) | parser never crashes on arbitrary text; manifest resume is idempotent |
| Integration | full run with a scripted fake LLM, over all 3 mediators × 3 p values, asserting the expected telemetry |
| Golden | one small cell with fixed seed and cached responses reproduces byte-identical metrics |
| Contract | a single `Mediator` conformance test suite run against all three implementations |
| Data | the three cell-integrity checks as a function used both in CI and at run time |

---

## 8. Weekly schedule at a glance

| Week | Main work | Done when |
|---|---|---|
| 1 | Resolve D1. Read Yang, Ji, Debenedetti. Repo skeleton | benchmarks located, repo builds |
| 2–3 | Env setup, schema, loaders, subsets | smoke tests pass, subset hashes written |
| 4 | Frontier choice, telemetry, start injector | `docs/frontier_choice.md` complete |
| 5–6 | Injector, ReAct loop, tool stubs | fake-LLM integration test green |
| 6–8 | None/MAC/IBAC, classifier, pre-registration | mediator contract tests pass, `prereg-v1` tagged (M2) |
| 7–9 | Pilot, power calibration, freeze | `exp-v1` tagged, budget table filled |
| 9–13 | Full ToolPrivBench grid | 18 cells pass integrity checks |
| 12–14 | AgentDojo grid | 6 cells pass integrity checks |
| 14–16 | Statistics, SHAP | every table/figure regenerates from `make analyse` |
| 15–19 | Dissertation | submission |

Note the overlaps: A4 and A5 overlap in W7–8, and A6 and A7 in W12–13. Keep the frontier arm running while you build the AgentDojo pipeline.

---

## 9. Biggest risks, in order

1. **Benchmark/baseline availability (D1)**: find out in Week 1.
2. **AgentDojo integration (D12)**: it has its own pipeline, so "used unchanged" needs care. Start the spike in Week 5, not Week 12.
3. **Llama throughput**: AgentDojo prompts are long and 4,050 runs is the biggest compute item. Measure in the pilot, then decide whether to fire L2.
4. **Scoring a "violation" correctly**: if your scoring does not match Yang et al., the baseline of ≈ 0.35 will not reproduce. Check at p = 0 in the pilot.
5. **Frontier API calls per run (D9)**: more calls per run than assumed would stretch the Phase 4 timeline.
6. **Unattended-run corruption**: covered by atomic writes + resume + integrity checks. Test by killing a batch mid-run.

---

## 10. First-week checklist

- [ ] Locate ToolPrivBench, SEAgent and AgentDojo code and data (D1). Note licences.
- [ ] Create the repo, `uv init`, `ollama pull`, run the §3.5 smoke tests.
- [ ] Read the ToolPrivBench paper for scoring rules and the scenario format.
- [ ] Open `docs/decisions.md` and answer D2–D8 and D11 in writing.
- [ ] Prototype the ReAct loop against one scenario with a real Llama call.
