"""Power analysis: can the design detect a 12-point difference in violation rate? (#27)

The analysis the plan describes (O1) compares two cells with a paired Wilcoxon test on the 50
scenario-level means, each mean taken over the seeds. This module simulates exactly that, many
times, to find how often a true difference of a given size is detected.

The simulated data follow the plan's recipe, a Beta-Binomial model with three layers:

1. **Scenarios differ.** Each scenario has its own true violation rate, drawn from a Beta
   distribution with the baseline mean (0.35 in the plan) and a between-scenario spread.
2. **Runs of one scenario differ.** Each run's rate is drawn around the scenario's rate with an
   intra-run correlation (Beta), because the calls in one run are not independent.
3. **Calls are counted.** A run with n calls has a Binomial number of violations, so its observed
   rate is a fraction of n. n is drawn from the pilot's own distribution of calls per run.

The noise (between-scenario spread and intra-run correlation) is estimated from the pilot by
method of moments (``estimate_noise``). With only 10 pilot scenarios these estimates are rough, so
the report also stresses the run-to-run noise (the variance of one scenario's runs) by 1.5 and 2
times. That is the noise that matters here: the test compares each scenario with itself, so the
scenarios' own true rates cancel out of the difference. (More between-scenario spread does not
lower power; in the Beta model it even shrinks each run's binomial noise a little.)

A true difference of ``effect`` is added to the second cell's scenario rates (clipped to the unit
interval). Power is the share of replicates in which the Wilcoxon test is significant. It is
reported at two significance levels: 0.05, and 0.05 / 18, the level the smallest of 18 p-values
must beat under Holm-Bonferroni (a conservative stand-in for the 18-cell family; the true Holm
power for one effect also depends on the other 17 tests). With ``effect`` = 0 the same code
measures the false-positive rate, which should be about the nominal level and is reported as a
check on the simulation.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict
from scipy import stats

BASELINE = 0.35  # the published rate with no failures (plan: baseline 0.35)
EFFECT = 0.12  # the minimum detectable effect the study was designed for (12 points)
FAMILY = 18  # the Holm family size (plan)
ALPHAS = (0.05, 0.05 / FAMILY)
TARGET_POWER = 0.80
N_SCENARIOS = 50
DESIGNS = ("paired", "did")  # a two-cell comparison, and the four-cell primary contrast
MIN_VARIANCE = 1e-4  # floor for an estimated variance that came out zero or negative

Ints = NDArray[np.int_]


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


class NoiseModel(_Frozen):
    """Noise estimated from the pilot, in the terms the simulation uses."""

    baseline: float  # mean violation rate used for the simulation
    pilot_mean: float  # the pilot's own mean rate, for comparison
    between_sd: float  # standard deviation of the scenarios' true rates
    rho: float  # correlation between calls inside one run (Beta-Binomial)
    calls: tuple[int, ...]  # the pilot's calls per run, sampled from in the simulation
    n_scenarios: int  # scenarios the estimate is based on
    runs_per_scenario: float

    def scaled_rho(self, factor: float) -> float:
        """The intra-run correlation that makes the run-to-run variance ``factor`` times the
        estimated one. It cannot go below the pure binomial noise, so a factor under about 0.5
        is capped there."""
        calls = np.asarray(self.calls, dtype=float)
        inv_n = float(np.mean(1.0 / calls))
        shrink = float(np.mean((calls - 1.0) / calls))
        if shrink <= 0:
            return self.rho
        scaled = (factor * (inv_n + self.rho * shrink) - inv_n) / shrink
        return float(min(max(scaled, 1e-6), 0.99))


def estimate_noise(
    summaries: pd.DataFrame, *, baseline: float = BASELINE, failure_rate: float = 0.0
) -> NoiseModel:
    """Estimate the noise from pilot run summaries at one failure rate (default: none).

    ``summaries`` has one row per run with ``scenario_id``, ``p``, ``total_calls`` and
    ``violation_rate``. Runs with no calls have no rate and are left out. Runs of every mediator
    at that failure rate are pooled as repeats of their scenario.
    """
    needed = {"scenario_id", "p", "total_calls", "violation_rate"}
    if needed - set(summaries.columns):
        raise ValueError(f"summaries has no column(s) {sorted(needed - set(summaries.columns))}")
    ref = summaries[(summaries["p"] == failure_rate) & summaries["violation_rate"].notna()]
    ref = ref[ref["total_calls"] > 0]
    per_scenario = ref.groupby("scenario_id")["violation_rate"]
    counts = per_scenario.size()
    if len(counts) < 3 or (counts < 2).any():
        raise ValueError("need at least 3 scenarios with at least 2 runs each to estimate noise")
    pilot_mean = float(ref["violation_rate"].mean())
    within = float(per_scenario.var(ddof=1).mean())  # run-to-run variance inside a scenario
    means = per_scenario.mean()
    runs = float(counts.mean())
    between_var = max(float(means.var(ddof=1)) - within / runs, MIN_VARIANCE)
    between_var = min(between_var, 0.95 * baseline * (1 - baseline))
    calls = ref["total_calls"].astype(int).to_numpy()
    inv_n = float(np.mean(1.0 / calls))
    shrink = float(np.mean((calls - 1) / calls))
    typical = baseline * (1 - baseline) - between_var  # average of theta * (1 - theta)
    rho = (within / typical - inv_n) / shrink if shrink > 0 else 0.0
    rho = float(min(max(rho, 1e-6), 0.99))
    return NoiseModel(
        baseline=baseline,
        pilot_mean=pilot_mean,
        between_sd=float(np.sqrt(between_var)),
        rho=rho,
        calls=tuple(int(c) for c in calls),
        n_scenarios=len(counts),
        runs_per_scenario=runs,
    )


def _beta(
    rng: np.random.Generator,
    mean: NDArray[np.float64],
    concentration: float | NDArray[np.float64],
    size: tuple[int, ...],
) -> NDArray[np.float64]:
    a = mean * concentration
    b = (1.0 - mean) * concentration
    return rng.beta(a, b, size=size)


def simulate_differences(
    noise: NoiseModel,
    *,
    effect: float,
    seeds: int,
    n_rep: int,
    n_scenarios: int = N_SCENARIOS,
    noise_scale: float = 1.0,
    design: str = "paired",
    rng: np.random.Generator,
) -> NDArray[np.float64]:
    """Scenario-level differences for ``n_rep`` simulated studies, one row per study.

    ``design`` is ``"paired"`` (second cell minus first: the plain two-cell comparison) or
    ``"did"`` (the primary contrast: the change in a second model's pair of cells minus the change
    in a first model's pair, four cells in all, with ``effect`` added to the one cell that
    carries the difference). The four-cell contrast has about twice the noise of the two-cell one.
    ``noise_scale`` multiplies the run-to-run variance of one scenario's runs (1 = as estimated).
    """
    if design not in DESIGNS:
        raise ValueError(f"design must be one of {DESIGNS}, got {design!r}")
    if seeds < 1 or n_rep < 1 or n_scenarios < 1:
        raise ValueError("seeds, n_rep and n_scenarios must be at least 1")
    if noise_scale <= 0:
        raise ValueError("noise_scale must be positive")
    mu = noise.baseline
    between_var = min(noise.between_sd**2, 0.95 * mu * (1 - mu))
    kappa = mu * (1 - mu) / max(between_var, MIN_VARIANCE) - 1.0
    theta = _beta(rng, np.full((n_rep, n_scenarios), mu), kappa, (n_rep, n_scenarios))
    theta = np.clip(theta, 1e-3, 1 - 1e-3)
    calls = np.asarray(noise.calls, dtype=int)
    rho = noise.scaled_rho(noise_scale)
    concentration = (1.0 - rho) / rho
    shape = (n_rep, n_scenarios, seeds)

    def scenario_means(true_rate: NDArray[np.float64]) -> NDArray[np.float64]:
        run_rate = _beta(rng, np.repeat(true_rate[..., None], seeds, axis=2), concentration, shape)
        n = rng.choice(calls, size=shape)
        violations = rng.binomial(n, np.clip(run_rate, 0.0, 1.0))
        return np.asarray((violations / n).mean(axis=2), dtype=float)

    shifted = np.clip(theta + effect, 1e-3, 1 - 1e-3)
    if design == "paired":
        return scenario_means(shifted) - scenario_means(theta)
    first_change = scenario_means(theta) - scenario_means(theta)
    second_change = scenario_means(shifted) - scenario_means(theta)
    return second_change - first_change


def wilcoxon_pvalues(differences: NDArray[np.float64]) -> NDArray[np.float64]:
    """Two-sided Wilcoxon signed-rank p-value of each row; 1 where every difference is zero."""
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        p = np.asarray(stats.wilcoxon(differences, axis=1).pvalue, dtype=float)
    p[np.isnan(p)] = 1.0
    return p


class PowerResult(_Frozen):
    design: str
    effect: float
    seeds: int
    noise_scale: float
    n_rep: int
    power: tuple[float, ...]  # one per alpha, in the order of ``alphas``
    alphas: tuple[float, ...]


def simulate_power(
    noise: NoiseModel,
    *,
    effect: float = EFFECT,
    seeds: int = 3,
    n_rep: int = 10_000,
    alphas: Sequence[float] = ALPHAS,
    noise_scale: float = 1.0,
    n_scenarios: int = N_SCENARIOS,
    design: str = "paired",
    seed: int,
) -> PowerResult:
    """Share of simulated studies in which the Wilcoxon test is significant, per alpha.

    With ``effect`` = 0 this is the false-positive rate. The seed is required, so the same inputs
    always give the same result.
    """
    rng = np.random.default_rng(seed)
    diff = simulate_differences(
        noise,
        effect=effect,
        seeds=seeds,
        n_rep=n_rep,
        n_scenarios=n_scenarios,
        noise_scale=noise_scale,
        design=design,
        rng=rng,
    )
    p = wilcoxon_pvalues(diff)
    return PowerResult(
        design=design,
        effect=effect,
        seeds=seeds,
        noise_scale=noise_scale,
        n_rep=n_rep,
        power=tuple(float(np.mean(p < a)) for a in alphas),
        alphas=tuple(alphas),
    )


def minimum_detectable_effect(
    noise: NoiseModel,
    *,
    alpha: float,
    seeds: int,
    target: float = TARGET_POWER,
    effects: Sequence[float] = tuple(np.round(np.arange(0.04, 0.2401, 0.02), 2)),
    n_rep: int = 2_000,
    noise_scale: float = 1.0,
    design: str = "paired",
    seed: int,
) -> float | None:
    """Smallest effect on the grid whose power reaches ``target`` (linearly interpolated between
    grid points), or ``None`` if even the largest does not."""
    previous: tuple[float, float] | None = None
    for effect in effects:
        power = simulate_power(
            noise, effect=float(effect), seeds=seeds, n_rep=n_rep, alphas=(alpha,),
            noise_scale=noise_scale, design=design, seed=seed,
        ).power[0]  # fmt: skip
        if power >= target:
            if previous is None or power == previous[1]:
                return float(effect)
            x0, y0 = previous
            return float(x0 + (target - y0) * (effect - x0) / (power - y0))
        previous = (float(effect), power)
    return None


# ---- the report ----------------------------------------------------------------------------

DESIGN_TITLES = {
    "paired": "Plain two-cell comparison (the plan's paired Wilcoxon contrast)",
    "did": "Primary contrast: difference in differences (four cells)",
}
ALPHA_LABELS = ("0.05", "0.05/18")


@dataclass(frozen=True)
class PowerReport:
    noise: NoiseModel
    grid: list[PowerResult]  # designs x seeds x noise scales, at the designed effect
    null: list[PowerResult]  # no true difference: the false-positive check
    mde: dict[tuple[str, int, str], float | None]  # (design, seeds, alpha label) -> effect
    seed_options: tuple[int, ...]
    scales: tuple[float, ...]
    runs_per_seed: int


def build_report(
    noise: NoiseModel,
    *,
    seed: int,
    n_rep: int = 10_000,
    mde_rep: int = 2_000,
    seed_options: Sequence[int] = (3, 5),
    scales: Sequence[float] = (1.0, 1.5, 2.0),
    effect: float = EFFECT,
    runs_per_seed: int = 450,
) -> PowerReport:
    """Power for both designs, the false-positive check, and the smallest detectable effects.

    ``runs_per_seed`` is the number of runs one more seed per scenario adds across the grid for
    one model (50 scenarios x 9 cells = 450), used to state what extra seeds cost.
    """
    grid = [
        simulate_power(
            noise, effect=effect, seeds=s, n_rep=n_rep, noise_scale=sc, design=d, seed=seed
        )
        for d in DESIGNS
        for s in seed_options
        for sc in scales
    ]
    null = [
        simulate_power(noise, effect=0.0, seeds=s, n_rep=n_rep, design=d, seed=seed)
        for d in DESIGNS
        for s in seed_options
    ]
    mde: dict[tuple[str, int, str], float | None] = {}
    for d in DESIGNS:
        for s in seed_options:
            for a, label in zip(ALPHAS, ALPHA_LABELS, strict=True):
                mde[(d, s, label)] = minimum_detectable_effect(
                    noise, alpha=a, seeds=s, n_rep=mde_rep, design=d, seed=seed
                )
    return PowerReport(noise, grid, null, mde, tuple(seed_options), tuple(scales), runs_per_seed)


def _pp(value: float | None) -> str:
    return "above 24 points" if value is None else f"{value * 100:.1f} points"


def _power(report: PowerReport, design: str, seeds: int, scale: float, alpha_index: int) -> float:
    for r in report.grid:
        if (r.design, r.seeds, r.noise_scale) == (design, seeds, scale):
            return r.power[alpha_index]
    raise KeyError((design, seeds, scale))


def render_markdown(report: PowerReport) -> str:
    """The report as Markdown. Every number comes from the report; nothing is typed in."""
    n = report.noise
    low, high = min(report.seed_options), max(report.seed_options)
    n_rep = report.grid[0].n_rep
    parts = [
        "# Power analysis (#27)\n",
        "Generated by `scripts/power_analysis.py`. Do not edit by hand.\n",
        f"A simulated study of {N_SCENARIOS} scenarios, each cell the mean over seeds, tested with "
        f"a paired Wilcoxon test, {n_rep:,} replicates per row. A true difference of "
        f"{EFFECT * 100:.0f} points is added. Two significance levels are shown: 0.05, and "
        f"0.05 / {FAMILY} = {ALPHAS[1]:.4f}, the level the smallest of 18 p-values must beat under "
        "Holm-Bonferroni (a conservative stand-in for the 18-cell family).\n",
        "## Noise estimated from the pilot\n",
        f"- {n.n_scenarios} pilot scenarios at no failure injection, "
        f"{n.runs_per_scenario:.1f} runs each (all mediators pooled).\n"
        f"- Pilot mean violation rate {n.pilot_mean:.3f}; the simulation uses the plan's baseline "
        f"{n.baseline:.2f}.\n"
        f"- Spread of scenarios' true rates (standard deviation): {n.between_sd:.3f}.\n"
        f"- Correlation between calls inside a run: {n.rho:.3f}"
        + (
            " (at its floor: the pilot shows no run-to-run noise beyond counting error)"
            if n.rho < 1e-3
            else ""
        )
        + f". Calls per run: mean {np.mean(n.calls):.1f}, from {len(n.calls)} pilot runs.\n\n"
        "With this few scenarios the noise is a rough estimate, so the tables also show the "
        "run-to-run variance made 1.5 and 2 times larger. The scenarios' own spread does not "
        "lower power, because each scenario is compared with itself.\n",
    ]
    for design in DESIGNS:
        parts.append(
            f"## {DESIGN_TITLES[design]}: power for a {EFFECT * 100:.0f}-point difference\n"
        )
        rows = [
            "| Seeds | Run-to-run noise | Power at 0.05 | Power at 0.05/18 |",
            "|---|---|---|---|",
        ]
        for r in (g for g in report.grid if g.design == design):
            rows.append(f"| {r.seeds} | x{r.noise_scale:g} | {r.power[0]:.1%} | {r.power[1]:.1%} |")
        parts.append("\n".join(rows) + "\n")
    parts.append("## Check: false positives with no true difference\n")
    rows = ["| Design | Seeds | Rejected at 0.05 | Rejected at 0.05/18 |", "|---|---|---|---|"]
    for r in report.null:
        rows.append(f"| {r.design} | {r.seeds} | {r.power[0]:.1%} | {r.power[1]:.2%} |")
    parts.append(
        "The simulation should reject about 5 % and at most about 0.28 % of the time.\n\n"
        + "\n".join(rows)
        + "\n"
    )
    parts.append(f"## Smallest difference detected with {TARGET_POWER:.0%} power (noise x1)\n")
    rows = ["| Design | Seeds | At 0.05 | At 0.05/18 |", "|---|---|---|---|"]
    for design in DESIGNS:
        for s in report.seed_options:
            rows.append(
                f"| {design} | {s} | {_pp(report.mde[(design, s, '0.05')])} "
                f"| {_pp(report.mde[(design, s, '0.05/18')])} |"
            )
    parts.append("\n".join(rows) + "\n")
    parts.append("## Decision rule (plan)\n")
    paired = _power(report, "paired", low, 1.0, 1)
    did = _power(report, "did", low, 1.0, 0)
    ok = paired >= TARGET_POWER and did >= TARGET_POWER
    parts.append(
        f"The plan: if power is below {TARGET_POWER:.0%}, move to {high} seeds. With {low} seeds "
        f"(noise x1): the plain comparison at 0.05/18 has {paired:.1%}; the primary "
        f"difference-in-differences at 0.05 has {did:.1%}. "
        + (
            f"Both reach {TARGET_POWER:.0%}: keep {low} seeds."
            if ok
            else f"At least one is below {TARGET_POWER:.0%}: move to {high} seeds."
        )
        + "\n"
    )
    paired_high = _power(report, "paired", high, 1.0, 1)
    did_high = _power(report, "did", high, 1.0, 0)
    parts.append(
        f"With {high} seeds: {paired_high:.1%} and {did_high:.1%}. If the run-to-run noise is "
        f"twice the estimate, {high} seeds give "
        f"{_power(report, 'paired', high, max(report.scales), 1):.1%} and "
        f"{_power(report, 'did', high, max(report.scales), 0):.1%}.\n"
    )
    extra = (high - low) * report.runs_per_seed
    parts.append(
        f"Cost of {high} instead of {low} seeds: {extra:,} more runs per model "
        f"({high / low - 1:.0%} more time and calls, since both are linear in runs).\n"
    )
    parts.append(
        "\nThis is the power to detect a difference of the designed size, not a forecast of the "
        "true effect. If the true effect is smaller, a non-significant result is reported as "
        "'any effect is smaller than the figure above', not as no effect. The primary contrast is "
        "simulated with the same noise for all four cells, which is an approximation (a model "
        "with a much lower baseline rate would have less counting noise).\n"
    )
    return "\n".join(parts)


def write_report(report: PowerReport, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(report))
    return path
