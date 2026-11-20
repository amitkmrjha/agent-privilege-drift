"""The power analysis against data with known noise. No run data, no model."""

import numpy as np
import pandas as pd
import pytest

from privilege_drift.analysis.power import (
    ALPHAS,
    NoiseModel,
    build_report,
    estimate_noise,
    minimum_detectable_effect,
    render_markdown,
    simulate_power,
    wilcoxon_pvalues,
)


def known_summaries(
    *, between_sd: float, rho: float, n_scenarios: int = 300, runs: int = 6, seed: int = 0
) -> pd.DataFrame:
    """Run summaries generated from a Beta-Binomial model with the given noise, at p = 0."""
    rng = np.random.default_rng(seed)
    mu = 0.35
    kappa = mu * (1 - mu) / between_sd**2 - 1
    calls = np.array([3, 4, 5, 6])
    rows = []
    for i in range(n_scenarios):
        theta = rng.beta(mu * kappa, (1 - mu) * kappa)
        for r in range(runs):
            run_rate = rng.beta(theta * (1 - rho) / rho, (1 - theta) * (1 - rho) / rho)
            n = int(rng.choice(calls))
            v = int(rng.binomial(n, run_rate))
            rows.append(
                {
                    "scenario_id": f"S{i}",
                    "p": 0.0,
                    "total_calls": n,
                    "violation_rate": v / n,
                    "run": r,
                }  # fmt: skip
            )
    return pd.DataFrame(rows)


@pytest.fixture
def noise() -> NoiseModel:
    return estimate_noise(known_summaries(between_sd=0.15, rho=0.3))


# ---- estimating the noise ------------------------------------------------------------------


def test_the_noise_estimate_recovers_the_known_values() -> None:
    noise = estimate_noise(known_summaries(between_sd=0.15, rho=0.3))
    assert noise.between_sd == pytest.approx(0.15, abs=0.025)
    assert noise.rho == pytest.approx(0.3, abs=0.08)
    assert noise.baseline == 0.35 and noise.n_scenarios == 300
    assert noise.pilot_mean == pytest.approx(0.35, abs=0.03)


def test_pure_binomial_noise_gives_a_near_zero_correlation() -> None:
    noise = estimate_noise(known_summaries(between_sd=0.15, rho=0.001))
    assert noise.rho < 0.06


def test_the_estimate_needs_enough_data() -> None:
    few = known_summaries(between_sd=0.15, rho=0.3, n_scenarios=2)
    with pytest.raises(ValueError, match="at least 3 scenarios"):
        estimate_noise(few)
    with pytest.raises(ValueError, match="no column"):
        estimate_noise(few.drop(columns=["total_calls"]))
    with pytest.raises(ValueError, match="at least 3 scenarios"):
        estimate_noise(known_summaries(between_sd=0.15, rho=0.3).assign(p=0.3))  # no p = 0 runs


def test_runs_with_no_calls_are_left_out() -> None:
    data = known_summaries(between_sd=0.15, rho=0.3, n_scenarios=20)
    data.loc[data.index[:30], ["total_calls", "violation_rate"]] = [0, float("nan")]
    assert len(estimate_noise(data).calls) == len(data) - 30


# ---- the simulation ------------------------------------------------------------------------


def test_with_no_true_difference_the_false_positive_rate_matches_the_level(
    noise: NoiseModel,
) -> None:
    result = simulate_power(noise, effect=0.0, seeds=3, n_rep=3000, seed=1)
    assert result.power[0] == pytest.approx(0.05, abs=0.02)
    assert result.power[1] < 0.01  # at 0.05 / 18


def test_a_large_difference_is_always_found(noise: NoiseModel) -> None:
    assert simulate_power(noise, effect=0.3, seeds=3, n_rep=500, seed=2).power[0] > 0.99


def test_power_rises_with_the_effect_and_with_seeds_and_falls_with_noise(
    noise: NoiseModel,
) -> None:
    def power(effect: float, seeds: int = 3, scale: float = 1.0) -> float:
        return simulate_power(
            noise,
            effect=effect,
            seeds=seeds,
            noise_scale=scale,
            n_rep=1500,
            alphas=(0.05,),
            seed=3,
        ).power[0]

    assert power(0.04) < power(0.08) < power(0.16)
    assert power(0.06, seeds=5) >= power(0.06, seeds=3) - 0.02
    assert power(0.06, scale=2.0) < power(0.06, scale=1.0)


def test_scaling_the_noise_scales_the_run_to_run_variance(noise: NoiseModel) -> None:
    assert noise.scaled_rho(1.0) == pytest.approx(noise.rho, abs=1e-9)
    assert noise.scaled_rho(2.0) > noise.scaled_rho(1.5) > noise.rho
    assert noise.scaled_rho(0.01) == pytest.approx(1e-6)  # cannot go below pure binomial noise
    calls = np.asarray(noise.calls, dtype=float)
    inv_n, shrink = float(np.mean(1 / calls)), float(np.mean((calls - 1) / calls))

    def variance(rho: float) -> float:
        return inv_n + rho * shrink

    assert variance(noise.scaled_rho(1.5)) / variance(noise.rho) == pytest.approx(1.5)


def test_the_scenarios_own_spread_does_not_lower_power(noise: NoiseModel) -> None:
    # Each scenario is compared with itself, so a wider spread of true rates cancels out.
    wide = noise.model_copy(update={"between_sd": noise.between_sd * 1.5})
    narrow = noise.model_copy(update={"between_sd": noise.between_sd * 0.5})

    def power(model: NoiseModel) -> float:
        return simulate_power(model, effect=0.06, n_rep=1500, alphas=(0.05,), seed=3).power[0]

    assert power(wide) >= power(narrow) - 0.03


def test_the_same_seed_gives_the_same_result(noise: NoiseModel) -> None:
    a = simulate_power(noise, effect=0.1, n_rep=300, seed=9)
    b = simulate_power(noise, effect=0.1, n_rep=300, seed=9)
    assert a == b


def test_all_zero_differences_have_p_one() -> None:
    p = wilcoxon_pvalues(np.vstack([np.zeros(50), np.linspace(0.1, 0.5, 50)]))
    assert p[0] == 1.0 and p[1] < 0.001


def test_bad_arguments_are_refused(noise: NoiseModel) -> None:
    with pytest.raises(ValueError, match="at least 1"):
        simulate_power(noise, seeds=0, n_rep=10, seed=0)
    with pytest.raises(ValueError, match="positive"):
        simulate_power(noise, noise_scale=0.0, n_rep=10, seed=0)


# ---- the smallest detectable effect and the report -----------------------------------------


def test_the_smallest_detectable_effect_is_larger_at_the_stricter_level(
    noise: NoiseModel,
) -> None:
    loose = minimum_detectable_effect(noise, alpha=ALPHAS[0], seeds=3, n_rep=600, seed=4)
    strict = minimum_detectable_effect(noise, alpha=ALPHAS[1], seeds=3, n_rep=600, seed=4)
    assert loose is not None and strict is not None
    assert 0.04 <= loose <= strict <= 0.24


def test_no_detectable_effect_on_the_grid_gives_none(noise: NoiseModel) -> None:
    assert (
        minimum_detectable_effect(
            noise, alpha=ALPHAS[1], seeds=3, effects=(0.001, 0.002), n_rep=200, seed=5
        )
        is None
    )


def test_the_report_states_the_decision_rule(noise: NoiseModel) -> None:
    report = build_report(noise, seed=6, n_rep=300, mde_rep=150)
    text = render_markdown(report)
    for heading in (
        "# Power analysis",
        "## Noise estimated from the pilot",
        "## Plain two-cell comparison",
        "## Primary contrast: difference in differences",
        "## Check: false positives",
        "## Decision rule",
    ):
        assert heading in text
    assert ("keep 3 seeds" in text) or ("move to 5 seeds" in text)
    assert "900 more runs per model" in text  # (5 - 3) x 450
    assert len(report.grid) == 2 * 2 * 3  # designs x seeds x noise scales
    assert len(report.null) == 2 * 2
    assert {r.design for r in report.grid} == {"paired", "did"}


# ---- the four-cell primary contrast --------------------------------------------------------


def test_the_primary_contrast_has_less_power_than_the_plain_comparison(
    noise: NoiseModel,
) -> None:
    def power(design: str) -> float:
        return simulate_power(
            noise, effect=0.08, n_rep=1500, alphas=(0.05,), design=design, seed=11
        ).power[0]

    assert power("did") < power("paired")  # four noisy cells, not two


def test_the_primary_contrast_also_has_the_right_false_positive_rate(
    noise: NoiseModel,
) -> None:
    result = simulate_power(noise, effect=0.0, n_rep=3000, design="did", seed=12)
    assert result.design == "did"
    assert result.power[0] == pytest.approx(0.05, abs=0.02)


def test_an_unknown_design_is_refused(noise: NoiseModel) -> None:
    with pytest.raises(ValueError, match="design must be"):
        simulate_power(noise, design="triple", n_rep=10, seed=0)
