"""Statistics for the pre-registered analysis (plan section O1, issue #36).

Every function here takes plain numbers or a pandas object and returns a small frozen result. None
of them reads run files or calls a model, so each can be checked against known values.

The unit of analysis is the scenario: ``scenario_means`` averages the seeds of one scenario in one
cell, which gives one value per scenario per cell (n = 50 for the experiment). Tests that compare
two cells pair those values by scenario id.

Nothing is dropped silently. A scenario that is missing from one side, or has no value, raises a
``ValueError`` so the caller decides what to do (a run with no tool calls has no violation rate,
D11).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Literal

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike, NDArray
from pydantic import BaseModel, ConfigDict
from scipy import stats
from statsmodels.stats.multitest import multipletests

Floats = NDArray[np.float64]


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


# ---- scenario-level values -----------------------------------------------------------------


def scenario_means(
    runs: pd.DataFrame, value: str, by: Sequence[str] = ("cell_id",)
) -> pd.DataFrame:
    """Mean of ``value`` over the seeds of each scenario, one column per cell.

    ``runs`` has one row per run, with ``scenario_id``, the ``by`` columns and ``value``. The
    result has one row per scenario and one column per distinct combination of the ``by`` columns.
    A run whose value is missing is left out of its scenario's mean.
    """
    missing = {"scenario_id", value, *by} - set(runs.columns)
    if missing:
        raise ValueError(f"runs has no column(s) {sorted(missing)}")
    return runs.pivot_table(index="scenario_id", columns=list(by), values=value, aggfunc="mean")


def _aligned(series: Sequence[pd.Series]) -> list[Floats]:
    """The values of each series as arrays in the same scenario order. Strict: no silent drops."""
    if not series:
        raise ValueError("nothing to align")
    first = series[0]
    for s in series:
        if not s.index.is_unique:
            raise ValueError("a series has repeated scenario ids")
        if set(s.index) != set(first.index):
            raise ValueError("the series cover different scenarios")
        if s.isna().any():
            raise ValueError("a scenario has no value; decide how to treat it before testing")
    order = sorted(first.index)
    if not order:
        raise ValueError("no scenarios")
    return [s.loc[order].to_numpy(dtype=float) for s in series]


# ---- paired tests --------------------------------------------------------------------------


class WilcoxonResult(_Frozen):
    statistic: float
    p_value: float
    n: int  # scenarios compared
    n_nonzero: int  # scenarios whose two values differ (the test ignores the others)


def paired_wilcoxon(a: pd.Series, b: pd.Series) -> WilcoxonResult:
    """Two-sided Wilcoxon signed-rank test on the per-scenario differences ``a - b``.

    SciPy's defaults apply (zero differences are dropped). If every difference is zero there is
    nothing to test and the p-value is 1.
    """
    x, y = _aligned([a, b])
    nonzero = int(np.count_nonzero(x - y))
    if nonzero == 0:
        return WilcoxonResult(statistic=0.0, p_value=1.0, n=len(x), n_nonzero=0)
    result = stats.wilcoxon(x, y)
    return WilcoxonResult(
        statistic=float(result.statistic),
        p_value=float(result.pvalue),
        n=len(x),
        n_nonzero=nonzero,
    )


class PageResult(_Frozen):
    statistic: float
    p_value: float
    n: int  # scenarios (rows)
    k: int  # ordered conditions (columns)


def page_trend(table: pd.DataFrame) -> PageResult:
    """Page's trend test: do values rise across the columns, taken in the order given?

    ``table`` has one row per scenario and one column per condition, columns in increasing order
    of the condition (for example failure rate 0, 0.3, 0.6). The alternative is an increasing
    trend. Needs at least three columns.
    """
    if table.shape[1] < 3:
        raise ValueError("Page's trend test needs at least three ordered conditions")
    if table.isna().any().any():
        raise ValueError("a scenario has no value in some condition")
    result = stats.page_trend_test(table.to_numpy(dtype=float))
    return PageResult(
        statistic=float(result.statistic),
        p_value=float(result.pvalue),
        n=int(table.shape[0]),
        k=int(table.shape[1]),
    )


# ---- effect sizes --------------------------------------------------------------------------

Magnitude = Literal["negligible", "small", "medium", "large"]


def cliffs_delta(x: ArrayLike, y: ArrayLike) -> float:
    """Cliff's delta: P(x > y) - P(x < y) over every pair, between -1 and 1.

    Written out here, with no library, because the plan asks for it to be unit-tested. Ties count
    as neither greater nor smaller.
    """
    a = np.asarray(x, dtype=float).ravel()
    b = np.asarray(y, dtype=float).ravel()
    if a.size == 0 or b.size == 0:
        raise ValueError("Cliff's delta needs at least one value on each side")
    greater = int(np.count_nonzero(a[:, None] > b[None, :]))
    smaller = int(np.count_nonzero(a[:, None] < b[None, :]))
    return (greater - smaller) / (a.size * b.size)


def cliffs_magnitude(delta: float) -> Magnitude:
    """Romano et al.'s labels for |delta|: below 0.147 negligible, 0.33 small, 0.474 medium."""
    size = abs(delta)
    if size < 0.147:
        return "negligible"
    if size < 0.33:
        return "small"
    if size < 0.474:
        return "medium"
    return "large"


def cohens_dz(a: pd.Series, b: pd.Series) -> float:
    """Cohen's d for paired values: mean of the differences over their standard deviation.

    Returns 0 when every difference is the same constant of zero, and raises when the differences
    are all equal but not zero (the standard deviation is zero, so d is not defined).
    """
    x, y = _aligned([a, b])
    diff = x - y
    if len(diff) < 2:
        raise ValueError("Cohen's d needs at least two scenarios")
    spread = float(np.std(diff, ddof=1))
    mean = float(np.mean(diff))
    if spread == 0.0:
        if mean == 0.0:
            return 0.0
        raise ValueError("every difference is the same non-zero value; d is not defined")
    return mean / spread


def cohens_d(x: ArrayLike, y: ArrayLike) -> float:
    """Cohen's d for two independent groups, using the pooled standard deviation."""
    a = np.asarray(x, dtype=float).ravel()
    b = np.asarray(y, dtype=float).ravel()
    if a.size < 2 or b.size < 2:
        raise ValueError("Cohen's d needs at least two values in each group")
    pooled_var = ((a.size - 1) * np.var(a, ddof=1) + (b.size - 1) * np.var(b, ddof=1)) / (
        a.size + b.size - 2
    )
    if pooled_var == 0.0:
        if float(np.mean(a)) == float(np.mean(b)):
            return 0.0
        raise ValueError("both groups are constant; d is not defined")
    return float((np.mean(a) - np.mean(b)) / np.sqrt(pooled_var))


# ---- multiple comparisons ------------------------------------------------------------------


class HolmResult(_Frozen):
    alpha: float
    reject: tuple[bool, ...]
    p_adjusted: tuple[float, ...]


def holm(p_values: Sequence[float], alpha: float = 0.05) -> HolmResult:
    """Holm-Bonferroni across one family of tests. Results are in the order of ``p_values``."""
    if not p_values:
        raise ValueError("no p-values")
    if any(not 0.0 <= p <= 1.0 for p in p_values):
        raise ValueError("every p-value must be between 0 and 1")
    reject, adjusted, _, _ = multipletests(list(p_values), alpha=alpha, method="holm")
    return HolmResult(
        alpha=alpha,
        reject=tuple(bool(r) for r in reject),
        p_adjusted=tuple(float(p) for p in adjusted),
    )


# ---- bootstrap -----------------------------------------------------------------------------


class BootstrapCI(_Frozen):
    estimate: float  # the statistic on the original, unresampled scenarios
    low: float
    high: float
    confidence: float
    n_boot: int
    seed: int


def bootstrap_ci(
    n_units: int,
    statistic: Callable[[NDArray[np.intp]], float],
    *,
    seed: int,
    n_boot: int = 10_000,
    confidence: float = 0.95,
) -> BootstrapCI:
    """Percentile bootstrap over scenarios.

    ``statistic`` receives an array of scenario positions (0 to ``n_units`` - 1, repeats allowed)
    and returns one number, so a statistic that uses several paired series resamples them
    together. The seed is required: the same inputs and seed always give the same interval.
    """
    if n_units < 1:
        raise ValueError("need at least one scenario to resample")
    if n_boot < 1:
        raise ValueError("n_boot must be at least 1")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, n_units, size=(n_boot, n_units))
    values = np.array([statistic(row) for row in draws], dtype=float)
    tail = (1.0 - confidence) / 2.0
    low, high = np.quantile(values, [tail, 1.0 - tail])
    return BootstrapCI(
        estimate=float(statistic(np.arange(n_units, dtype=np.intp))),
        low=float(low),
        high=float(high),
        confidence=confidence,
        n_boot=n_boot,
        seed=seed,
    )


# ---- the pre-registered primary contrast ---------------------------------------------------


def difference_in_differences(
    *,
    llama_low: pd.Series,
    llama_high: pd.Series,
    frontier_low: pd.Series,
    frontier_high: pd.Series,
    seed: int,
    n_boot: int = 10_000,
    confidence: float = 0.95,
) -> BootstrapCI:
    """(frontier delta) minus (Llama delta), where delta = violation rate at the high failure
    rate minus the rate at the low one, both under no mediator.

    The four inputs are per-scenario means (``scenario_means``), indexed by scenario id. A positive
    estimate means the frontier model's escalation rose more than Llama's. The interval resamples
    scenarios, keeping each scenario's four values together.
    """
    ll, lh, fl, fh = _aligned([llama_low, llama_high, frontier_low, frontier_high])
    llama_delta = lh - ll
    frontier_delta = fh - fl

    def statistic(idx: NDArray[np.intp]) -> float:
        return float(np.mean(frontier_delta[idx]) - np.mean(llama_delta[idx]))

    return bootstrap_ci(len(ll), statistic, seed=seed, n_boot=n_boot, confidence=confidence)
