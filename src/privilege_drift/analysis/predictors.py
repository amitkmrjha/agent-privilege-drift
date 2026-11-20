"""RQ3: which failure signals predict that the next proposed call escalates? (#39)

Input is the table of call records (``telemetry.load_calls``): one row per tool call the model
proposed. The predictors were computed from earlier calls only (D24), so none of them can see the
call's own outcome. The label is D5:

- ``primary``: the proposed call's tier is above the scenario's minimum tier (``is_violation``);
- ``secondary``: its tier is above every earlier call in the run (``escalated_above_prior``).

Method, as in the plan (section O3):

1. Build one row per call from five signals: the rolling 503 rate, retries since the last
   success, what the agent saw as the previous result (``error_surface``, one-hot), the step
   index, and the reasoning tokens so far. Constant columns are dropped and reported.
2. Compute the variance inflation factor (VIF). Features above the threshold (5) are replaced by
   their first principal component, so overlapping signals share one weight instead of splitting
   it arbitrarily. The component is fitted without the labels.
3. Logistic regression, tested leave-scenario-out with ``GroupKFold(5)``: every call of a scenario
   is on the same side of the split, so the test never reuses a scenario seen in training. AUC and
   a calibration table are computed from the out-of-fold predictions.
4. Importance = mean absolute SHAP value of the logistic model (``shap.LinearExplainer``) on
   standardised features, so weights are comparable across features.
5. A bootstrap over scenarios (1,000 replicates in the plan) refits the model on resampled
   scenarios and gives intervals for each importance and for each feature's rank.

Nothing here reads files or calls a model. A replicate whose resample has only one label class
cannot be fitted and is skipped and counted.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy.stats import rankdata
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant

SIGNALS = ("rolling_503_rate", "retry_since_success", "step_idx", "reasoning_tokens_cum")
ERROR_SURFACES = ("success", "service_unavailable", "blocked", "tool_error")  # "none" is the base
LABELS = {"primary": "is_violation", "secondary": "escalated_above_prior"}
VIF_THRESHOLD = 5.0
COMPONENT = "pc_collinear"
CV_SPLITS = 5
CALIBRATION_BINS = 10

Floats = NDArray[np.float64]


@dataclass(frozen=True)
class Table:
    """The modelling table: features, the 0/1 label, and the scenario each row belongs to."""

    X: pd.DataFrame
    y: NDArray[np.int_]
    groups: NDArray[np.str_]


def feature_table(calls: pd.DataFrame, label: str = "primary") -> Table:
    """One row per proposed call, with the signals as columns."""
    if label not in LABELS:
        raise ValueError(f"label must be one of {sorted(LABELS)}, got {label!r}")
    needed = {*SIGNALS, "error_surface", "scenario_id", LABELS[label]}
    missing = needed - set(calls.columns)
    if missing:
        raise ValueError(f"calls has no column(s) {sorted(missing)}")
    if calls.empty:
        raise ValueError("no calls")
    unknown = set(calls["error_surface"]) - {"none", *ERROR_SURFACES}
    if unknown:
        raise ValueError(f"unknown error_surface value(s): {sorted(unknown)}")
    X = calls[list(SIGNALS)].astype(float).reset_index(drop=True)
    for surface in ERROR_SURFACES:
        X[f"surface_{surface}"] = (calls["error_surface"] == surface).astype(float).to_numpy()
    y = calls[LABELS[label]].astype(int).to_numpy()
    groups = calls["scenario_id"].astype(str).to_numpy()
    return Table(X=X, y=y, groups=groups)


# ---- overlapping features ------------------------------------------------------------------


def vif_table(X: pd.DataFrame) -> pd.DataFrame:
    """Variance inflation factor of each column (infinite when a column is a combination of the
    others)."""
    if X.shape[1] < 2:
        return pd.DataFrame({"feature": list(X.columns), "vif": [1.0] * X.shape[1]})
    values = add_constant(X.to_numpy(dtype=float), has_constant="add")
    with np.errstate(divide="ignore", invalid="ignore"):
        vifs = [float(variance_inflation_factor(values, i + 1)) for i in range(X.shape[1])]
    return pd.DataFrame({"feature": list(X.columns), "vif": vifs})


@dataclass(frozen=True)
class Collapsed:
    X: pd.DataFrame
    vif_before: pd.DataFrame
    collapsed: tuple[str, ...]  # the features replaced by the component
    dropped_constant: tuple[str, ...]
    explained_variance: float | None  # share of the collapsed features' variance it keeps


def collapse_collinear(X: pd.DataFrame, threshold: float = VIF_THRESHOLD) -> Collapsed:
    """Drop constant columns, then replace features with VIF above ``threshold`` by their first
    principal component (``pc_collinear``). A single high-VIF feature cannot be collapsed and is
    kept. The component's sign is fixed so it correlates positively with the first feature it
    replaces."""
    constant = tuple(c for c in X.columns if float(X[c].std(ddof=0)) == 0.0)
    kept = X.drop(columns=list(constant))
    vif = vif_table(kept)
    high = [str(f) for f, v in zip(vif["feature"], vif["vif"], strict=True) if v > threshold]
    if len(high) < 2:
        return Collapsed(kept, vif, (), constant, None)
    block = StandardScaler().fit_transform(kept[high].to_numpy(dtype=float))
    pca = PCA(n_components=1)
    component = pca.fit_transform(block)[:, 0]
    if float(np.corrcoef(component, block[:, 0])[0, 1]) < 0:
        component = -component
    out = kept.drop(columns=high)
    out[COMPONENT] = component
    return Collapsed(out, vif, tuple(high), constant, float(pca.explained_variance_ratio_[0]))


# ---- model, cross-validation, calibration --------------------------------------------------


def _fit(X: Floats, y: NDArray[np.int_]) -> tuple[Floats, Floats]:
    """Standardise and fit; returns the coefficients and the standardised features."""
    if len(np.unique(y)) < 2:
        raise ValueError("the label has only one class; there is nothing to predict")
    scaler = StandardScaler().fit(X)
    scaled = scaler.transform(X)
    model = LogisticRegression(max_iter=1000).fit(scaled, y)
    return np.asarray(model.coef_[0], dtype=float), np.asarray(scaled, dtype=float)


def calibration_table(
    probabilities: Floats, y: NDArray[np.int_], bins: int = CALIBRATION_BINS
) -> pd.DataFrame:
    """Predicted probability against the observed rate, in equal-width bins (empty bins omitted)."""
    index = np.minimum((probabilities * bins).astype(int), bins - 1)
    rows = []
    for b in range(bins):
        mask = index == b
        if mask.any():
            rows.append(
                {
                    "bin": b,
                    "mean_predicted": float(probabilities[mask].mean()),
                    "observed_rate": float(y[mask].mean()),
                    "n": int(mask.sum()),
                }
            )
    return pd.DataFrame(rows)


@dataclass(frozen=True)
class CvResult:
    n_rows: int
    n_positive: int
    n_scenarios: int
    n_splits: int
    auc: float | None  # None when the out-of-fold labels have one class
    fold_auc: tuple[float | None, ...]
    brier: float
    calibration: pd.DataFrame


def cross_validate(table: Table, n_splits: int = CV_SPLITS) -> CvResult:
    """Leave-scenario-out cross-validation (``GroupKFold``): AUC, Brier score and calibration."""
    n_scenarios = len(set(table.groups))
    splits = min(n_splits, n_scenarios)
    if splits < 2:
        raise ValueError("need at least two scenarios to cross-validate")
    X = table.X.to_numpy(dtype=float)
    out_of_fold = np.zeros(len(table.y))
    fold_auc: list[float | None] = []
    for train, test in GroupKFold(n_splits=splits).split(X, table.y, table.groups):
        if len(np.unique(table.y[train])) < 2:
            raise ValueError("a training fold has only one label class")
        scaler = StandardScaler().fit(X[train])
        model = LogisticRegression(max_iter=1000).fit(scaler.transform(X[train]), table.y[train])
        out_of_fold[test] = model.predict_proba(scaler.transform(X[test]))[:, 1]
        both = len(np.unique(table.y[test])) == 2
        fold_auc.append(float(roc_auc_score(table.y[test], out_of_fold[test])) if both else None)
    overall = float(roc_auc_score(table.y, out_of_fold)) if len(np.unique(table.y)) == 2 else None
    return CvResult(
        n_rows=len(table.y),
        n_positive=int(table.y.sum()),
        n_scenarios=n_scenarios,
        n_splits=splits,
        auc=overall,
        fold_auc=tuple(fold_auc),
        brier=float(brier_score_loss(table.y, out_of_fold)),
        calibration=calibration_table(out_of_fold, table.y),
    )


# ---- importance ----------------------------------------------------------------------------


def _mean_abs_shap(coef: Floats, scaled: Floats) -> Floats:
    """Mean absolute SHAP value of a logistic model on standardised features.

    For a linear model with independent features this is |coefficient| * mean |x - mean(x)|, which
    is what ``shap.LinearExplainer`` returns; ``importance_table`` computes both and a test checks
    they agree.
    """
    return np.asarray(np.abs(coef) * np.abs(scaled - scaled.mean(axis=0)).mean(axis=0), dtype=float)


def importance_table(table: Table) -> pd.DataFrame:
    """Coefficient and mean absolute SHAP value per feature, rank 1 = most important."""
    import shap  # imported here: it is slow to import and only this function needs it

    X = table.X.to_numpy(dtype=float)
    coef, scaled = _fit(X, table.y)
    model = LogisticRegression(max_iter=1000).fit(scaled, table.y)
    # SHAP averages over a random background sample of at most 100 rows by default. Use every row,
    # so the result does not depend on that sampling and equals the closed form in the bootstrap.
    background = shap.maskers.Independent(scaled, max_samples=len(scaled))
    explainer = shap.LinearExplainer(model, background)
    values = np.asarray(explainer.shap_values(scaled), dtype=float)
    importance = np.abs(values).mean(axis=0)
    return pd.DataFrame(
        {
            "feature": list(table.X.columns),
            "coef": coef,
            "mean_abs_shap": importance,
            "rank": rankdata(-importance, method="min").astype(int),
        }
    )


def bootstrap_importance(
    table: Table,
    *,
    seed: int,
    n_boot: int = 1_000,
    confidence: float = 0.95,
) -> tuple[pd.DataFrame, int]:
    """Bootstrap over scenarios: intervals for each feature's importance and rank.

    Each replicate resamples whole scenarios with replacement (all of a scenario's calls stay
    together), refits the model and recomputes the importances. Returns the intervals and the
    number of replicates skipped because their resample had a single label class.
    """
    if n_boot < 1:
        raise ValueError("n_boot must be at least 1")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")
    X = table.X.to_numpy(dtype=float)
    scenarios = sorted(set(table.groups))
    rows_of = {s: np.flatnonzero(table.groups == s) for s in scenarios}
    rng = np.random.default_rng(seed)
    importances: list[Floats] = []
    ranks: list[Floats] = []
    skipped = 0
    for _ in range(n_boot):
        chosen = rng.integers(0, len(scenarios), size=len(scenarios))
        index = np.concatenate([rows_of[scenarios[i]] for i in chosen])
        y = table.y[index]
        if len(np.unique(y)) < 2:
            skipped += 1
            continue
        coef, scaled = _fit(X[index], y)
        imp = _mean_abs_shap(coef, scaled)
        importances.append(imp)
        ranks.append(rankdata(-imp, method="min").astype(float))
    if not importances:
        raise ValueError("every bootstrap replicate had a single label class")
    tail = [(1.0 - confidence) / 2.0, 1.0 - (1.0 - confidence) / 2.0]
    imp_lo, imp_hi = np.quantile(np.array(importances), tail, axis=0)
    rank_lo, rank_hi = np.quantile(np.array(ranks), tail, axis=0)
    frame = pd.DataFrame(
        {
            "feature": list(table.X.columns),
            "imp_ci_low": imp_lo,
            "imp_ci_high": imp_hi,
            "rank_ci_low": rank_lo,
            "rank_ci_high": rank_hi,
        }
    )
    return frame, skipped


# ---- the report ----------------------------------------------------------------------------


@dataclass(frozen=True)
class PredictorReport:
    label: str
    collapse: Collapsed
    cv: CvResult
    importance: pd.DataFrame  # importance_table plus the bootstrap intervals
    skipped_replicates: int
    n_boot: int


def build_rq3(
    calls: pd.DataFrame,
    *,
    seed: int,
    label: str = "primary",
    n_boot: int = 1_000,
    vif_threshold: float = VIF_THRESHOLD,
) -> PredictorReport:
    """Everything RQ3 reports, for the calls given (subset by model or mediator before calling)."""
    base = feature_table(calls, label)
    collapse = collapse_collinear(base.X, vif_threshold)
    table = Table(X=collapse.X, y=base.y, groups=base.groups)
    cv = cross_validate(table)
    importance = importance_table(table)
    intervals, skipped = bootstrap_importance(table, seed=seed, n_boot=n_boot)
    merged = importance.merge(intervals, on="feature").sort_values("rank").reset_index(drop=True)
    return PredictorReport(label, collapse, cv, merged, skipped, n_boot)


def _fmt(value: object) -> str:
    if isinstance(value, float):
        return "n/a" if value != value else f"{value:.3f}"
    return str(value)


def _md_table(frame: pd.DataFrame, columns: Sequence[str]) -> str:
    if frame.empty:
        return "_No rows._\n"
    lines = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    for _, row in frame.iterrows():
        lines.append("| " + " | ".join(_fmt(row[c]) for c in columns) + " |")
    return "\n".join(lines) + "\n"


def render_markdown(report: PredictorReport) -> str:
    """The report as Markdown. Every number comes from the report; nothing is typed in."""
    cv, col = report.cv, report.collapse
    parts = [f"# RQ3: which signals predict escalation ({report.label} label)\n"]
    parts.append(
        f"{cv.n_rows} calls from {cv.n_scenarios} scenarios, {cv.n_positive} positive "
        f"({cv.n_positive / cv.n_rows:.1%}).\n"
    )
    parts.append("## Predictive performance (leave-scenario-out)\n")
    folds = ", ".join(_fmt(a) for a in cv.fold_auc)
    parts.append(
        f"- AUC {_fmt(cv.auc)} over {cv.n_splits} folds (per fold: {folds})\n"
        f"- Brier score {cv.brier:.3f}\n"
    )
    parts.append("\n### Calibration\n")
    parts.append(_md_table(cv.calibration, ["bin", "mean_predicted", "observed_rate", "n"]))
    parts.append("\n## Overlapping features\n")
    parts.append(_md_table(col.vif_before, ["feature", "vif"]))
    if col.collapsed:
        parts.append(
            f"\nReplaced by `{COMPONENT}` (keeps {col.explained_variance:.1%} of their "
            f"variance): {', '.join(col.collapsed)}.\n"
        )
    else:
        parts.append("\nNo feature set needed collapsing.\n")
    if col.dropped_constant:
        parts.append(f"\nConstant, dropped: {', '.join(col.dropped_constant)}.\n")
    parts.append("\n## Importance (mean absolute SHAP, standardised features)\n")
    parts.append(
        _md_table(
            report.importance,
            [
                "rank",
                "feature",
                "coef",
                "mean_abs_shap",
                "imp_ci_low",
                "imp_ci_high",
                "rank_ci_low",
                "rank_ci_high",
            ],
        )  # fmt: skip
    )
    parts.append(
        f"\nIntervals: bootstrap over scenarios, {report.n_boot} replicates"
        f" ({report.skipped_replicates} skipped for a single label class).\n"
    )
    return "\n".join(parts)


def plot_importance(report: PredictorReport, path: Path) -> Path:
    """Bar chart of mean absolute SHAP per feature with bootstrap intervals."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    frame = report.importance.sort_values("mean_abs_shap")
    fig, ax = plt.subplots(figsize=(6, 0.5 * len(frame) + 1.5))
    ax.barh(
        frame["feature"],
        frame["mean_abs_shap"],
        xerr=[
            (frame["mean_abs_shap"] - frame["imp_ci_low"]).clip(lower=0),
            (frame["imp_ci_high"] - frame["mean_abs_shap"]).clip(lower=0),
        ],
        capsize=3,
    )
    ax.set_xlabel("mean absolute SHAP value (standardised features)")
    ax.set_title(f"What predicts escalation ({report.label} label)")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
