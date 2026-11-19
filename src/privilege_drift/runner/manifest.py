"""The per-cell ``manifest.json``: what was run, under which settings, and how it ended."""

from __future__ import annotations

import subprocess
from datetime import datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from privilege_drift.telemetry import atomic_write_text

MANIFEST_NAME = "manifest.json"


class CellStatus(StrEnum):
    COMPLETE = "complete"  # every planned run has a valid result
    INCOMPLETE = "incomplete"  # some runs failed or were not reached; run the cell again


class Manifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    cell_id: str
    cell_idx: int
    model: str
    p: float
    mediator: str
    config_hash: str
    git_sha: str | None
    git_dirty: bool | None
    model_fingerprints: tuple[str, ...]  # one entry expected; more means the model changed mid-cell
    seeds: dict[str, tuple[int, ...]]  # scenario id -> the seeds used, in seed_idx order
    planned_runs: int
    completed_runs: int
    unfinished_runs: tuple[str, ...]  # no valid result yet (failed, or not reached)
    started_at: datetime
    finished_at: datetime
    status: CellStatus


def git_info(cwd: Path | None = None) -> tuple[str | None, bool | None]:
    """The commit and whether the working tree has uncommitted changes (None if no git)."""

    def git(*args: str) -> str | None:
        try:
            done = subprocess.run(
                ["git", *args], cwd=cwd, capture_output=True, text=True, check=True, timeout=10
            )
        except (OSError, subprocess.SubprocessError):
            return None
        return done.stdout.strip()

    sha = git("rev-parse", "HEAD")
    dirty = git("status", "--porcelain")
    return sha, (None if dirty is None else bool(dirty))


def write_manifest(manifest: Manifest, cell_dir: Path) -> Path:
    path = cell_dir / MANIFEST_NAME
    atomic_write_text(path, manifest.model_dump_json(indent=2) + "\n")
    return path


def read_manifest(cell_dir: Path) -> Manifest:
    return Manifest.model_validate_json((cell_dir / MANIFEST_NAME).read_text())
