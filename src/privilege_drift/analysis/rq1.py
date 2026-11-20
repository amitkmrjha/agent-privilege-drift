"""RQ1: does failure pressure raise the violation rate, and does it differ between models? (#37)

Input is the table of run summaries (``telemetry.load_summaries``): one row per run, with
``scenario_id``, ``model``, ``p``, ``mediator`` and ``violation_rate``. Everything is computed at
the scenario level (the mean over seeds, ``stats.scenario_means``), so each cell contributes one
value per scenario.

Sign conventions, fixed here so that a table is never read backwards:

- an "across p" contrast is the rate at the higher failure rate minus the rate at the lower one;
- a "between models" contrast is the second model minus the first (frontier minus Llama);
- the primary contrast is (frontier delta) minus (Llama delta), delta = rate at the high failure
  rate minus the rate at the low one, under no mediator.

A scenario with no value in one of the cells being compared (for example a run with no tool calls
has no violation rate, D11) is left out of that comparison and counted in ``n_excluded``, so it is
reported and never dropped silently.

Two choices the pre-registration (#29) must confirm, because the plan does not pin them down:
the Holm families (here: all across-p contrasts together, 18 for the full grid, and all
between-model contrasts together, 9), and the test behind the primary contrast's p-value (here: a
paired Wilcoxon test of the per-scenario deltas, frontier against Llama).
"""

from __future__ import annotations

import itertools
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict

from privilege_drift.analysis.stats import (
    BootstrapCI,
    bootstrap_ci,
    cliffs_delta,
    cliffs_magnitude,
    cohens_dz,
    difference_in_differences,
    holm,
    page_trend,
    paired_wilcoxon,
    scenario_means,
)

VALUE = "violation_rate"
CELL_KEYS = ("model", "p", "mediator")
DEFAULT_MODELS = ("llama", "frontier")
PRIMARY_MEDIATOR = "none"
TARGET_EFFECT = 0.12  # the 12-point minimum detectable effect the study was powered for

Key = tuple[str, float, str]  # (model, failure rate, mediator)


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


def scenario_table(summaries: pd.DataFrame) -> pd.DataFrame:
    """Violation rate per scenario (rows) and cell (columns keyed by model, p, mediator)."""
    return scenario_means(summaries, VALUE, by=CELL_KEYS)


def _complete(table: pd.DataFrame, *keys: Key) -> tuple[list[pd.Series], int]:
    """The named columns restricted to scenarios that have a value in all of them.

    Returns the columns and the number of scenarios left out because one was missing.
    """
    frame = pd.concat([table[k] for k in keys], axis=1).dropna()
    return [frame.iloc[:, i] for i in range(len(keys))], int(len(table.index) - len(frame))


# ---- rates ---------------------------------------------------------------------------------


def _mean_of(values: NDArray[np.float64]) -> Callable[[NDArray[np.intp]], float]:
    """A bootstrap statistic: the mean of the resampled scenarios' values."""

    def statistic(idx: NDArray[np.intp]) -> float:
        return float(values[idx].mean())

    return statistic


def rates_table(table: pd.DataFrame, *, seed: int, n_boot: int = 10_000) -> pd.DataFrame:
    """Mean violation rate per cell with a bootstrap interval over scenarios."""
    rows = []
    for model, p, mediator in table.columns:
        values = table[(model, p, mediator)].dropna().to_numpy(dtype=float)
        if len(values) == 0:
            continue
        ci = bootstrap_ci(len(values), _mean_of(values), seed=seed, n_boot=n_boot)
        rows.append(
            {
                "model": model,
                "p": p,
                "mediator": mediator,
                "n_scenarios": len(values),
                "mean": ci.estimate,
                "ci_low": ci.low,
                "ci_high": ci.high,
            }
        )
    return pd.DataFrame(rows).sort_values(["mediator", "model", "p"]).reset_index(drop=True)


# ---- contrasts -----------------------------------------------------------------------------


def _contrast_row(table: pd.DataFrame, kind: str, a: Key, b: Key) -> dict[str, object]:
    """One contrast a minus b, with its test and effect sizes."""
    (sa, sb), excluded = _complete(table, a, b)
    row: dict[str, object] = {
        "kind": kind,
        "mediator": a[2],
        "model_a": a[0],
        "p_a": a[1],
        "model_b": b[0],
        "p_b": b[1],
        "n": len(sa),
        "n_excluded": excluded,
    }
    nan = float("nan")
    if len(sa) == 0:
        return {**row, "mean_a": nan, "mean_b": nan, "diff": nan, "p_wilcoxon": nan,
                "cliffs_delta": nan, "magnitude": "", "cohens_dz": nan}  # fmt: skip
    try:
        dz = cohens_dz(sa, sb) if len(sa) > 1 else nan
    except ValueError:  # every difference identical and non-zero: d is not defined
        dz = nan
    delta = cliffs_delta(sa.to_numpy(), sb.to_numpy())
    return {
        **row,
        "mean_a": float(sa.mean()),
        "mean_b": float(sb.mean()),
        "diff": float(sa.mean() - sb.mean()),
        "p_wilcoxon": paired_wilcoxon(sa, sb).p_value,
        "cliffs_delta": delta,
        "magnitude": cliffs_magnitude(delta),
        "cohens_dz": dz,
    }


def contrasts_table(table: pd.DataFrame, models: Sequence[str] = DEFAULT_MODELS) -> pd.DataFrame:
    """Every across-p contrast within a model and every between-model contrast at each p.

    Holm-adjusted p-values are added within each kind: ``across_p`` is one family and
    ``between_models`` another.
    """
    present = set(table.columns)
    mediators = sorted({m for _, _, m in present})
    ps = sorted({p for _, p, _ in present})
    rows: list[dict[str, object]] = []
    for model, mediator in itertools.product(models, mediators):
        for low, high in itertools.combinations(ps, 2):
            a, b = (model, high, mediator), (model, low, mediator)
            if a in present and b in present:
                rows.append(_contrast_row(table, "across_p", a, b))
    for p, mediator in itertools.product(ps, mediators):
        for first, second in itertools.combinations(models, 2):
            a, b = (second, p, mediator), (first, p, mediator)
            if a in present and b in present:
                rows.append(_contrast_row(table, "between_models", a, b))
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["p_holm"] = float("nan")
    frame["reject_holm"] = False
    for _, group in frame.groupby("kind"):
        usable = group["p_wilcoxon"].notna()
        index = group.index[usable]
        if len(index) == 0:
            continue
        result = holm(group.loc[index, "p_wilcoxon"].tolist())
        frame.loc[index, "p_holm"] = list(result.p_adjusted)
        frame.loc[index, "reject_holm"] = list(result.reject)
    return frame


# ---- trend and primary contrast ------------------------------------------------------------


def page_table(table: pd.DataFrame, models: Sequence[str] = DEFAULT_MODELS) -> pd.DataFrame:
    """Page's trend test across the ordered failure rates, per model and mediator."""
    present = set(table.columns)
    ps = sorted({p for _, p, _ in present})
    rows = []
    for model, mediator in itertools.product(models, sorted({m for _, _, m in present})):
        keys = [(model, p, mediator) for p in ps]
        if len(keys) < 3 or not all(k in present for k in keys):
            continue
        frame = pd.concat([table[k] for k in keys], axis=1).dropna()
        if len(frame) < 2:  # Page's test needs at least two scenarios with every rate present
            continue
        frame.columns = pd.Index([str(p) for p in ps])
        result = page_trend(frame)
        rows.append(
            {
                "model": model,
                "mediator": mediator,
                "n": result.n,
                "k": result.k,
                "L": result.statistic,
                "p_value": result.p_value,
            }
        )
    return pd.DataFrame(rows)


class PrimaryContrast(_Frozen):
    """The pre-registered difference in differences, under no mediator."""

    mediator: str
    low_p: float
    high_p: float
    n_scenarios: int
    n_excluded: int
    llama_delta: float
    frontier_delta: float
    did: BootstrapCI  # frontier delta minus Llama delta
    p_wilcoxon: float  # paired, per-scenario deltas: frontier against Llama
    cohens_dz: float | None
    cliffs_delta: float
    magnitude: str


def primary_contrast(
    table: pd.DataFrame,
    *,
    seed: int,
    n_boot: int = 10_000,
    mediator: str = PRIMARY_MEDIATOR,
    models: Sequence[str] = DEFAULT_MODELS,
    low_p: float | None = None,
    high_p: float | None = None,
) -> PrimaryContrast | None:
    """The primary contrast, or ``None`` if a model or failure rate it needs is not in the data."""
    first, second = models[0], models[1]
    ps = sorted({p for _, p, _ in table.columns})
    if len(ps) < 2:
        return None
    low = ps[0] if low_p is None else low_p
    high = ps[-1] if high_p is None else high_p
    keys = [(first, low, mediator), (first, high, mediator), (second, low, mediator),
            (second, high, mediator)]  # fmt: skip
    if not all(k in set(table.columns) for k in keys):
        return None
    (ll, lh, fl, fh), excluded = _complete(table, *keys)
    if len(ll) == 0:
        return None
    did = difference_in_differences(
        llama_low=ll, llama_high=lh, frontier_low=fl, frontier_high=fh, seed=seed, n_boot=n_boot
    )
    llama_delta, frontier_delta = lh - ll, fh - fl
    try:
        dz: float | None = cohens_dz(frontier_delta, llama_delta) if len(ll) > 1 else None
    except ValueError:
        dz = None
    delta = cliffs_delta(frontier_delta.to_numpy(), llama_delta.to_numpy())
    return PrimaryContrast(
        mediator=mediator,
        low_p=low,
        high_p=high,
        n_scenarios=len(ll),
        n_excluded=excluded,
        llama_delta=float(llama_delta.mean()),
        frontier_delta=float(frontier_delta.mean()),
        did=did,
        p_wilcoxon=paired_wilcoxon(frontier_delta, llama_delta).p_value,
        cohens_dz=dz,
        cliffs_delta=delta,
        magnitude=cliffs_magnitude(delta),
    )


# ---- the report ----------------------------------------------------------------------------


@dataclass(frozen=True)
class Rq1Report:
    rates: pd.DataFrame
    contrasts: pd.DataFrame
    page: pd.DataFrame
    primary: PrimaryContrast | None


def build_rq1(
    summaries: pd.DataFrame,
    *,
    seed: int,
    n_boot: int = 10_000,
    models: Sequence[str] = DEFAULT_MODELS,
) -> Rq1Report:
    """All RQ1 numbers from the run summaries."""
    table = scenario_table(summaries)
    return Rq1Report(
        rates=rates_table(table, seed=seed, n_boot=n_boot),
        contrasts=contrasts_table(table, models),
        page=page_table(table, models),
        primary=primary_contrast(table, seed=seed, n_boot=n_boot, models=models),
    )


def _fmt(value: object) -> str:
    if isinstance(value, float):
        return "n/a" if value != value else f"{value:.3f}"
    return str(value)


def _markdown_table(frame: pd.DataFrame, columns: Sequence[str]) -> str:
    if frame.empty:
        return "_No rows._\n"
    lines = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    for _, row in frame.iterrows():
        lines.append("| " + " | ".join(_fmt(row[c]) for c in columns) + " |")
    return "\n".join(lines) + "\n"


def render_markdown(report: Rq1Report, *, target: float = TARGET_EFFECT) -> str:
    """The report as Markdown. Every number comes from the report; nothing is typed in."""
    parts = ["# RQ1: failure pressure and escalation\n"]
    parts.append("## Violation rate by cell\n")
    parts.append(
        _markdown_table(
            report.rates, ["mediator", "model", "p", "n_scenarios", "mean", "ci_low", "ci_high"]
        )
    )
    parts.append("## Primary contrast\n")
    prim = report.primary
    if prim is None:
        parts.append("_Not computed: needs both models at two failure rates under no mediator._\n")
    else:
        did = prim.did
        parts.append(
            f"Failure rate {prim.low_p:g} to {prim.high_p:g}, mediator `{prim.mediator}`, "
            f"{prim.n_scenarios} scenarios ({prim.n_excluded} excluded for missing values).\n\n"
            f"- Llama delta: {prim.llama_delta:.3f}; frontier delta: {prim.frontier_delta:.3f}\n"
            f"- Difference in differences (frontier minus Llama): **{did.estimate:.3f}**, "
            f"{did.confidence:.0%} bootstrap interval [{did.low:.3f}, {did.high:.3f}]\n"
            f"- Paired Wilcoxon p = {prim.p_wilcoxon:.4f}; Cliff's delta = {prim.cliffs_delta:.3f}"
            f" ({prim.magnitude}); Cohen's dz = {_fmt(prim.cohens_dz)}\n"
        )
        bound = max(abs(did.low), abs(did.high))
        if bound < target:
            parts.append(
                f"\nThe interval lies inside +/-{target:.2f}: the data rule out a difference "
                f"as large as the {target:.0%}-point target, and any real difference is at most "
                f"{bound:.3f} (an upper bound, not an estimate).\n"
            )
        else:
            parts.append(
                f"\nThe interval reaches {bound:.3f}, so a difference as large as the "
                f"{target:.0%}-point target is not ruled out.\n"
            )
    parts.append("\n## Contrasts (Holm within each kind)\n")
    parts.append(
        _markdown_table(
            report.contrasts,
            [
                "kind",
                "mediator",
                "model_a",
                "p_a",
                "model_b",
                "p_b",
                "n",
                "n_excluded",
                "diff",
                "p_wilcoxon",
                "p_holm",
                "reject_holm",
                "cliffs_delta",
                "magnitude",
                "cohens_dz",
            ],
        )  # fmt: skip
    )
    parts.append("\n## Page's trend across failure rates\n")
    parts.append(_markdown_table(report.page, ["model", "mediator", "n", "k", "L", "p_value"]))
    return "\n".join(parts)


def plot_rates(rates: pd.DataFrame, path: Path) -> Path:
    """Violation rate against failure rate, one line per model, one panel per mediator."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    mediators = sorted(rates["mediator"].unique())
    fig, axes = plt.subplots(1, len(mediators), figsize=(4 * len(mediators), 3.2), squeeze=False)
    for ax, mediator in zip(axes[0], mediators, strict=True):
        for model, group in rates[rates["mediator"] == mediator].groupby("model"):
            group = group.sort_values("p")
            ax.errorbar(
                group["p"],
                group["mean"],
                yerr=[group["mean"] - group["ci_low"], group["ci_high"] - group["mean"]],
                marker="o",
                capsize=3,
                label=str(model),
            )
        ax.set_title(f"mediator: {mediator}")
        ax.set_xlabel("injected failure rate")
        ax.set_ylim(0, 1)
    axes[0][0].set_ylabel("violation rate")
    axes[0][0].legend()
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
