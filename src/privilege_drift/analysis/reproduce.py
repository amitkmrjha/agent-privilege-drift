"""One command that regenerates every analysis number, table and figure (#41).

``run_analysis(runs, out)`` reads only the finished run files under ``runs/<cell id>/`` and writes

    out/numbers.json          every number quoted in writing comes from here
    out/tables/*.csv          the tables behind them
    out/figures/*.png         the figures
    out/rq1.md, out/rq2.md, out/rq3_*.md  the readable reports

The outputs contain no timestamps, no absolute paths and no machine details, and every random
step uses the seed given, so the same run files and settings always give byte-identical files
(a test checks this). ``numbers.json`` records a digest of the input files so a result can be tied
to the exact data it came from.

A part that cannot be computed yet (for example RQ3 when no call has the positive label) is
recorded in ``numbers.json`` as ``{"skipped": <reason>}`` instead of stopping the rest, so the
command is usable on a batch that is still going. The AgentDojo analysis (#40) is not part of this
yet. IBAC classifier accuracy needs the benchmark's domain labels; if the downloaded benchmark file
is present its hash is recorded in ``numbers.json`` and accuracy is computed, otherwise it is
left out.

Choices the pre-registration (#29) should confirm: RQ3 is fitted once on every call found, for
both labels, not per model or mediator (use ``scripts/rq3_report.py --model --mediator`` for
those).
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from privilege_drift.analysis import predictors, rq1, rq2
from privilege_drift.data import DataError
from privilege_drift.data.toolprivbench import DEFAULT_PATH as BENCHMARK_PATH
from privilege_drift.data.toolprivbench import load_toolprivbench
from privilege_drift.runner import is_finished
from privilege_drift.subsets import MASTER_SEED
from privilege_drift.telemetry import load_calls, load_summaries, run_path

DEFAULT_RUNS = Path("runs")
DEFAULT_OUT = Path("results")
RQ3_LABELS = ("primary", "secondary")


def finished_runs(runs: Path) -> list[Path]:
    """Main result files of every finished run under ``runs/<cell id>/``, in a fixed order."""
    paths: list[Path] = []
    for directory in sorted(p for p in runs.iterdir() if p.is_dir()):
        for file in sorted(directory.glob("*.jsonl")):
            if file.name.endswith(".raw.jsonl") or file.name.startswith("infrastructure"):
                continue
            run_id = file.name.removesuffix(".jsonl")
            if is_finished(directory, run_id):
                paths.append(run_path(directory, run_id))
    return paths


def inputs_digest(paths: list[Path]) -> str:
    """SHA-256 over every input file's relative name and content, in a fixed order."""
    digest = hashlib.sha256()
    for path in paths:
        digest.update(f"{path.parent.name}/{path.name}\n".encode())
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _clean(value: Any) -> Any:
    """Plain JSON types: NaN and infinity become null, NumPy scalars become Python numbers."""
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_clean(v) for v in value]
    if hasattr(value, "item") and not isinstance(value, str | bytes):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return _clean(frame.to_dict(orient="records"))  # type: ignore[no-any-return]


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def _analyse_rq1(summaries: pd.DataFrame, out: Path, *, seed: int, n_boot: int) -> dict[str, Any]:
    try:
        report = rq1.build_rq1(summaries, seed=seed, n_boot=n_boot)
    except ValueError as exc:
        return {"skipped": str(exc)}
    _write_csv(report.rates, out / "tables" / "rq1_rates.csv")
    _write_csv(report.contrasts, out / "tables" / "rq1_contrasts.csv")
    _write_csv(report.page, out / "tables" / "rq1_page.csv")
    (out / "rq1.md").write_text(rq1.render_markdown(report))
    if not report.rates.empty:
        rq1.plot_rates(report.rates, out / "figures" / "rq1.png")
    return {
        "rates": _records(report.rates),
        "contrasts": _records(report.contrasts),
        "page": _records(report.page),
        "primary": None if report.primary is None else _clean(report.primary.model_dump()),
    }


def _benchmark_domains(path: Path = BENCHMARK_PATH) -> tuple[dict[str, str] | None, str | None]:
    """Each scenario's domain label and the benchmark file's hash, or (None, None) if the file
    has not been downloaded."""
    if not path.is_file():
        return None, None
    try:
        domains = {s.id: s.domain for s in load_toolprivbench(path)}
    except DataError:
        return None, None
    return domains, hashlib.sha256(path.read_bytes()).hexdigest()


def _analyse_rq2(
    summaries: pd.DataFrame,
    out: Path,
    *,
    seed: int,
    n_boot: int,
    domains: dict[str, str] | None,
) -> Any:
    try:
        report = rq2.build_rq2(summaries, seed=seed, n_boot=n_boot, domains=domains)
    except ValueError as exc:
        return {"skipped": str(exc)}
    _write_csv(report.metrics, out / "tables" / "rq2_metrics.csv")
    _write_csv(report.contrasts, out / "tables" / "rq2_contrasts.csv")
    _write_csv(report.floor, out / "tables" / "rq2_floor.csv")
    _write_csv(report.classifier, out / "tables" / "rq2_classifier.csv")
    (out / "rq2.md").write_text(rq2.render_markdown(report))
    if not report.metrics.empty:
        rq2.plot_metrics(report.metrics, out / "figures" / "rq2.png")
    return _clean(
        {
            "metrics": _records(report.metrics),
            "contrasts": _records(report.contrasts),
            "floor": _records(report.floor),
            "floor_points": report.floor_points,
            "classifier": _records(report.classifier),
            "classifier_accuracy": report.accuracy,
        }
    )


def _analyse_rq3(calls: pd.DataFrame, out: Path, label: str, *, seed: int, n_boot: int) -> Any:
    try:
        report = predictors.build_rq3(calls, seed=seed, label=label, n_boot=n_boot)
    except ValueError as exc:
        return {"skipped": str(exc)}
    _write_csv(report.importance, out / "tables" / f"rq3_{label}_importance.csv")
    _write_csv(report.cv.calibration, out / "tables" / f"rq3_{label}_calibration.csv")
    (out / f"rq3_{label}.md").write_text(predictors.render_markdown(report))
    predictors.plot_importance(report, out / "figures" / f"rq3_{label}.png")
    cv = report.cv
    return _clean(
        {
            "n_rows": cv.n_rows,
            "n_positive": cv.n_positive,
            "n_scenarios": cv.n_scenarios,
            "auc": cv.auc,
            "fold_auc": cv.fold_auc,
            "brier": cv.brier,
            "collapsed": report.collapse.collapsed,
            "dropped_constant": report.collapse.dropped_constant,
            "explained_variance": report.collapse.explained_variance,
            "skipped_replicates": report.skipped_replicates,
            "importance": _records(report.importance),
        }
    )


def run_analysis(
    runs: Path = DEFAULT_RUNS,
    out: Path = DEFAULT_OUT,
    *,
    seed: int = MASTER_SEED,
    n_boot_rq1: int = 10_000,
    n_boot_rq2: int = 10_000,
    n_boot_rq3: int = 1_000,
) -> dict[str, Any]:
    """Run every implemented analysis on the finished runs and write the outputs to ``out``."""
    paths = finished_runs(runs)
    if not paths:
        raise ValueError(f"no finished runs under {runs}")
    summaries = load_summaries(paths)
    calls = load_calls(paths)
    domains, benchmark_hash = _benchmark_domains()
    out.mkdir(parents=True, exist_ok=True)
    numbers: dict[str, Any] = {
        "inputs": {
            "n_runs": len(paths),
            "n_calls": int(len(calls)),
            "sha256": inputs_digest(paths),
            "benchmark_sha256": benchmark_hash,
        },
        "settings": {
            "seed": seed,
            "n_boot_rq1": n_boot_rq1,
            "n_boot_rq2": n_boot_rq2,
            "n_boot_rq3": n_boot_rq3,
        },
        "rq1": _analyse_rq1(summaries, out, seed=seed, n_boot=n_boot_rq1),
        "rq2": _analyse_rq2(summaries, out, seed=seed, n_boot=n_boot_rq2, domains=domains),
        "rq3": {
            label: _analyse_rq3(calls, out, label, seed=seed, n_boot=n_boot_rq3)
            for label in RQ3_LABELS
        }
        if not calls.empty
        else {"skipped": "no tool calls in the finished runs"},
    }
    (out / "numbers.json").write_text(
        json.dumps(_clean(numbers), indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return numbers
