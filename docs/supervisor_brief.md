# Supervisor brief: decisions needed before the pre-registration

Date: 2026-11-21. Project: *Dynamic Tool Authorization: least-privilege violations and privilege escalation under failure pressure in open-source agents*. PRD deadline: 2 December 2026.

## Where the project stands

The harness (agent, failure injector, three access-control arms, telemetry, batch runner) and the analysis code (RQ1, RQ2, RQ3, one-command reproduction) are built and tested. A 270-run pilot of the local model (Llama 3.1 8B) on 10 scenarios **outside** the frozen 50 ran cleanly: all integrity checks pass, every health rate is under 5 %, and with no failures and no mediator the violation rate is **34.7 %** against the benchmark paper's **about 35 %**, so the scoring is sound. The full local grid would take about 9 hours. Pilot numbers are tuning data, not results.

## What the pilot showed that affects the design

1. **IBAC and MAC make identical decisions on ToolPrivBench.** Its two tiers and its labels make every sensible IBAC policy equal MAC, so "IBAC vs MAC" is empty by construction here (the classifier is 84 to 90 % accurate, but its mistakes change nothing).
2. **The violation rate per call looked flat across failure rates** for Llama (34.7, 34.1, 34.5 %), while violating calls per run rose (1.17, 1.40, 1.70) because runs got longer. Which measure is primary matters, and a null result is possible.
3. **Power:** with 3 seeds the primary contrast has about 79 % power for a 12-point difference (80 % target), and detects about 12 points; 5 seeds would give 94 % but cost two-thirds more time. I have kept 3 seeds to keep the runs short.

## Decisions needed from you

| # | Decision | Options | Recommendation |
|---|---|---|---|
| 1 | **RQ2 stays as written; is that acceptable?** IBAC vs MAC is expected to be empty on ToolPrivBench, so the answer will be "no difference between IBAC and MAC here" | (a) keep RQ2 unchanged, run all three arms on Llama, and report that result plainly (recommended); (b) rest the IBAC claim on AgentDojo (not yet built, extra time); (c) reframe the question; (d) invent intent-specific policies (not recommended: manufactures a difference) | (a), with AgentDojo kept optional. Please check that the proposal's RQ2 sentence does not require both models; if it does, a one-line scope note ("tested on Llama") suffices |
| 2 | **Run plan (plan A)** | Full grid (2,700 runs) or **12 of 18 cells (1,800 runs, about 9.3 hours of Llama)**: Llama with no mediator, MAC and IBAC at three failure rates; frontier with no mediator only | Plan A. It keeps RQ1, RQ2 (unchanged) and RQ3 intact and saves 900 frontier runs; only frontier MAC and IBAC are not run |
| 3 | **What does 2 December cover?** | The experiments, or the whole thesis | Needed to decide whether the frontier arm can fit at all |
| 4 | **The pre-declared utility-floor wording** (proposal section 7.5.2) and how the 5-point floor is read | I read it as: IBAC's task success is not more than 5 points below the comparator, judged from a confidence interval | Please supply the wording and confirm the reading |
| 5 | **Primary violation measure** | Rate per call (as planned), with violating calls per run as a pre-registered secondary | Keep the per-call rate as primary; choose it on what it measures, not on the pilot's pattern |
| 6 | **Frontier baseline** | The model is currently a small, fast Gemini model with different decoding settings (the larger ones were unavailable or overloaded); a larger model would cost more quota | Is a small model acceptable as the "frontier baseline" for RQ1? |

## Risks

The frontier arm depends on an API quota that is not yet confirmed. The primary contrast is borderline-powered, so a non-significant result will be reported as an upper bound ("any difference is smaller than about 12 points"), not as no effect. The tool outputs are canned (no real side effects), and the tier map has two levels.

Detail: `docs/pilot.md`, `docs/power.md`, `docs/decisions/` (D26, D27, D28, D29, D30, D31).
