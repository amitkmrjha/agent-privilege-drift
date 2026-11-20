"""The freeze record: hashes of everything that must not change once the experiment starts (#30).

Two groups of files are hashed:

- **run** files decide what the experiment does (agent, prompt, parser, failure injector,
  mediators, model client, runner, telemetry, data and schema code, the configs, the frozen
  subset and seeds, and the dependency lock). Any change after the freeze is a deviation and goes in
  ``docs/deviations.md``.
- **analysis** files only read the finished runs. They are hashed too, so what changed after the
  freeze is visible, but a change there is a note, not a deviation of the experiment.

``freeze_record.json`` is written by ``scripts/freeze.py --prepare`` and checked by
``--verify`` and ``--tag``. The pre-registration's own text is hashed with its freeze-record
section removed (that section holds these hashes), so the registered text is covered too.
Nothing here runs git or reads the network.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path

from pydantic import BaseModel, ConfigDict

RUN_PATTERNS = (
    "src/privilege_drift/*.py",
    "src/privilege_drift/agent/*.py",
    "src/privilege_drift/data/*.py",
    "src/privilege_drift/failure/*.py",
    "src/privilege_drift/llm/*.py",
    "src/privilege_drift/mediators/*.py",
    "src/privilege_drift/runner/*.py",
    "src/privilege_drift/telemetry/*.py",
    "configs/grid.yaml",
    "configs/models.yaml",
    "configs/intents.yaml",
    "configs/policies/*.yaml",
    "configs/tiers/*.yaml",
    "prereg/seed_schedule.json",
    "prereg/subsets/*.json",
    "prereg/subsets/HASHES.txt",
    "pyproject.toml",
    "uv.lock",
)
ANALYSIS_PATTERNS = ("src/privilege_drift/analysis/*.py", "src/privilege_drift/metrics/*.py")
FREEZE_SECTION = "## 11. Freeze record"
RECORD_NAME = "freeze_record.json"
_MARKER = re.compile(r"\[(?:CONFIRM|FILL)[^\]]*\]")


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hash_files(root: Path, patterns: Sequence[str]) -> dict[str, str]:
    """SHA-256 of every file matching the patterns, keyed by its path relative to ``root``."""
    found: dict[str, str] = {}
    for pattern in patterns:
        for path in sorted(root.glob(pattern)):
            if path.is_file() and "__pycache__" not in path.parts:
                found[path.relative_to(root).as_posix()] = sha256_of(path)
    return dict(sorted(found.items()))


def combined_digest(hashes: Mapping[str, str]) -> str:
    """One SHA-256 over the sorted ``path  hash`` lines, so one number covers a whole group."""
    text = "\n".join(f"{path}  {digest}" for path, digest in sorted(hashes.items()))
    return hashlib.sha256(text.encode()).hexdigest()


def strip_freeze_section(text: str) -> str:
    """The pre-registration without its freeze-record section (the one that holds the hashes)."""
    index = text.find(FREEZE_SECTION)
    return text if index < 0 else text[:index].rstrip() + "\n"


def prereg_digest(text: str) -> str:
    return hashlib.sha256(strip_freeze_section(text).encode()).hexdigest()


def open_markers(text: str) -> list[tuple[int, str]]:
    """Each ``[CONFIRM ...]`` or ``[FILL ...]`` marker still in the registered text, as the 1-based
    line it starts on and that line's text. A marker may run over several lines. The freeze-record
    section is left out: its blanks are filled by the freeze itself."""
    body = strip_freeze_section(text)
    lines = body.splitlines()
    return [
        (number, lines[number - 1].strip())
        for number in (body.count("\n", 0, match.start()) + 1 for match in _MARKER.finditer(body))
    ]


class FreezeRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    tag: str
    code_commit: str  # the commit the hashes were taken at (the freeze commit is its child)
    created_utc: str
    run_files: dict[str, str]
    run_digest: str
    analysis_files: dict[str, str]
    analysis_digest: str
    prereg_digest: str
    benchmark_sha256: str
    frontier_model: str
    seeds_per_scenario: int
    max_steps: int
    window_k: int


def build_record(
    root: Path,
    *,
    tag: str,
    code_commit: str,
    created_utc: str,
    prereg_text: str,
    benchmark_sha256: str,
    frontier_model: str,
    seeds_per_scenario: int,
    max_steps: int,
    window_k: int,
) -> FreezeRecord:
    run_files = hash_files(root, RUN_PATTERNS)
    analysis_files = hash_files(root, ANALYSIS_PATTERNS)
    return FreezeRecord(
        tag=tag,
        code_commit=code_commit,
        created_utc=created_utc,
        run_files=run_files,
        run_digest=combined_digest(run_files),
        analysis_files=analysis_files,
        analysis_digest=combined_digest(analysis_files),
        prereg_digest=prereg_digest(prereg_text),
        benchmark_sha256=benchmark_sha256,
        frontier_model=frontier_model,
        seeds_per_scenario=seeds_per_scenario,
        max_steps=max_steps,
        window_k=window_k,
    )


def write_record(record: FreezeRecord, path: Path) -> None:
    path.write_text(json.dumps(record.model_dump(), indent=2, sort_keys=True) + "\n")


def read_record(path: Path) -> FreezeRecord:
    return FreezeRecord.model_validate_json(path.read_text())


class Drift(BaseModel):
    """What differs between the frozen record and the files on disk."""

    model_config = ConfigDict(frozen=True)

    run_changed: tuple[str, ...]
    run_added: tuple[str, ...]
    run_removed: tuple[str, ...]
    analysis_changed: tuple[str, ...]
    prereg_changed: bool

    @property
    def experiment_changed(self) -> bool:
        """True if anything that decides what the experiment does, or its registered text, moved."""
        return bool(self.run_changed or self.run_added or self.run_removed or self.prereg_changed)


def _diff(
    frozen: Mapping[str, str], now: Mapping[str, str]
) -> tuple[list[str], list[str], list[str]]:
    changed = sorted(p for p in frozen if p in now and frozen[p] != now[p])
    added = sorted(p for p in now if p not in frozen)
    removed = sorted(p for p in frozen if p not in now)
    return changed, added, removed


def compare(root: Path, record: FreezeRecord, prereg_text: str) -> Drift:
    """Compare the files now on disk with the frozen record."""
    run_changed, run_added, run_removed = _diff(record.run_files, hash_files(root, RUN_PATTERNS))
    analysis_changed, analysis_added, analysis_removed = _diff(
        record.analysis_files, hash_files(root, ANALYSIS_PATTERNS)
    )
    return Drift(
        run_changed=tuple(run_changed),
        run_added=tuple(run_added),
        run_removed=tuple(run_removed),
        analysis_changed=tuple(analysis_changed + analysis_added + analysis_removed),
        prereg_changed=prereg_digest(prereg_text) != record.prereg_digest,
    )


def freeze_section(record: FreezeRecord) -> str:
    """The pre-registration's freeze-record section, filled from the record."""
    return f"""{FREEZE_SECTION}

Written by `scripts/freeze.py --prepare`; checked by `--verify` (`make freeze-check`). The
machine-readable copy is `prereg/{RECORD_NAME}`.

| Item | Value |
|---|---|
| Tag | `{record.tag}` (created after this record is merged) |
| Code commit | `{record.code_commit}` |
| Recorded at (UTC) | {record.created_utc} |
| Run files digest | `{record.run_digest}` |
| Analysis code digest | `{record.analysis_digest}` |
| Registered text digest | `{record.prereg_digest}` |
| Benchmark file SHA-256 | `{record.benchmark_sha256}` |
| Frontier model | `{record.frontier_model}` |
| Seeds per scenario | {record.seeds_per_scenario} |
| Max steps | {record.max_steps} |
| Window k | {record.window_k} |

The run files digest covers {len(record.run_files)} files: the run-time code, the configs, the
frozen subset and seeds, and the dependency lock. The analysis digest covers
{len(record.analysis_files)} files and is recorded for visibility. The registered text digest
is this file without this section.

A change to a run file after the tag is a deviation and goes in `docs/deviations.md`; a change to
the analysis code is noted there too.
"""


def with_freeze_section(prereg_text: str, record: FreezeRecord) -> str:
    return strip_freeze_section(prereg_text) + "\n" + freeze_section(record)
