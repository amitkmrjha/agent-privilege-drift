"""Writing and reading a run's JSONL files.

A run is two files in the cell's directory: ``<run_id>.raw.jsonl`` (the model's replies) and
``<run_id>.jsonl`` (records and summary). Each is written to a temporary file and renamed, and
the main file is renamed last, so **the main file exists only for a run that finished**. The batch
runner (#21) can resume by checking for it, and a crash never leaves a half-written record.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterable
from pathlib import Path

import pandas as pd
from pydantic import TypeAdapter

from privilege_drift.telemetry.records import Record, RunTelemetry

_RECORD = TypeAdapter(Record)


def atomic_write_text(path: Path, text: str) -> None:
    """Write ``text`` to ``path`` so readers see either the old file or the whole new one."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def run_path(directory: Path, run_id: str) -> Path:
    return directory / f"{run_id}.jsonl"


def is_complete(directory: Path, run_id: str) -> bool:
    return run_path(directory, run_id).is_file()


def write_run(telemetry: RunTelemetry, directory: Path) -> Path:
    """Write a finished run's files and return the main file's path."""
    run_id = telemetry.summary.run_id
    raw = "".join(r.model_dump_json() + "\n" for r in telemetry.raw)
    atomic_write_text(directory / f"{run_id}.raw.jsonl", raw)
    main = "".join(r.model_dump_json() + "\n" for r in telemetry.records)
    path = run_path(directory, run_id)
    atomic_write_text(path, main)
    return path


def read_run(path: Path) -> RunTelemetry:
    """Load one run's main file. Raw replies are not loaded (see ``raw_response_ref``)."""
    records = tuple(
        _RECORD.validate_json(line) for line in path.read_text().splitlines() if line.strip()
    )
    return RunTelemetry(records=records, raw=())


def load_calls(paths: Iterable[Path]) -> pd.DataFrame:
    """Every ``call`` record of the given runs as one row each, in the order given."""
    rows = [c.model_dump(mode="json") for p in paths for c in read_run(p).calls]
    return pd.DataFrame(rows)


def load_summaries(paths: Iterable[Path]) -> pd.DataFrame:
    """One row per run, from each run's summary record."""
    return pd.DataFrame([read_run(p).summary.model_dump(mode="json") for p in paths])
