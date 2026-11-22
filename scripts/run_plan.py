"""Run one lane of the registered plan, cell by cell, in its pre-registered priority order (D31).

    uv run python scripts/run_plan.py --lane llama [--dry-run] [--limit N]
    make run-plan LANE=llama

For each cell of the lane it runs `privilege-drift run-cell`, then `check-cell`, and stops at the
first cell that fails, so a problem is seen at once rather than hours later. Cells are resumable:
run the same command again and finished runs are skipped. The order puts the primary contrast first
and the p = 0.3 mediator cells last, so a deadline or an exhausted quota cuts the least valuable
cells (a registered cell not finished is reported as "not run", per the pre-registration).

Before it starts it refuses unless: the freeze tag `exp-v2` exists, the run files still match the
freeze record, the working tree is clean (every manifest records whether it was), and the model
service it needs is reachable (Ollama for the Llama lane and for IBAC; the API key for the frontier
lane). `--limit N` runs at most N runs per cell and skips the integrity check, for a small trial.

The Llama lane and the frontier lanes use different resources, so they can run at the same time in
separate terminals. `--first N` runs only the first N cells of the lane in its priority order; the
exp-v2 amendment (D32) starts the `frontier_large` lane with `--first 3`, the no-mediator cells.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

import httpx

from privilege_drift.freeze_record import RECORD_NAME, compare, read_record
from privilege_drift.llm import load_models_config
from privilege_drift.runner import expand_cells, load_grid
from privilege_drift.runner.grid import Cell

ROOT = Path.cwd()
TAG = "exp-v2"  # the latest freeze (exp-v2 amends exp-v1, D32)

# D31, highest value first: the primary contrast, the other no-mediator cell, IBAC and MAC at the
# two ends of the failure range, then the middle failure rate for the mediators.
# Each entry is (mediator, failure rate).
PRIORITY: tuple[tuple[str, float], ...] = (
    ("none", 0.0),
    ("none", 0.6),
    ("none", 0.3),
    ("ibac", 0.0),
    ("ibac", 0.6),
    ("mac", 0.0),
    ("mac", 0.6),
    ("ibac", 0.3),
    ("mac", 0.3),
)


def lane_cells(cells: Sequence[Cell], model: str) -> list[Cell]:
    """One model's cells in the pre-registered order; a cell outside the order is an error."""
    mine = {(c.mediator, c.p): c for c in cells if c.model == model}
    unknown = set(mine) - set(PRIORITY)
    if unknown:
        raise ValueError(f"cells with no place in the priority order: {sorted(unknown)}")
    return [mine[key] for key in PRIORITY if key in mine]


def stamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def git(*args: str) -> str:
    done = subprocess.run(["git", *args], capture_output=True, text=True, check=True, cwd=ROOT)
    return done.stdout.strip()


def preflight(model: str, *, needs_ollama: bool) -> list[str]:
    """Reasons not to start, as short sentences. Empty means go."""
    problems: list[str] = []
    if git("tag", "--list", TAG) != TAG:
        problems.append(f"the freeze tag {TAG} does not exist")
    record = ROOT / "prereg" / RECORD_NAME
    if not record.is_file():
        problems.append("there is no freeze record")
    else:
        drift = compare(ROOT, read_record(record), (ROOT / "prereg/preregistration.md").read_text())
        if drift.experiment_changed:
            problems.append(
                "run files or the registered text differ from the freeze (make freeze-check)"
            )
    if git("status", "--porcelain"):
        problems.append("the working tree is not clean (manifests record that; commit or stash)")
    config = load_models_config()
    spec = config.spec(model)
    if spec.api_key_env and not os.environ.get(spec.api_key_env):
        problems.append(f"{spec.api_key_env} is not set (set -a; source .env; set +a)")
    if needs_ollama:
        base = os.environ.get("OLLAMA_API_BASE") or "http://localhost:11434"
        wanted = config.spec("llama").litellm_model.removeprefix("ollama/")
        try:
            names = [m["name"] for m in httpx.get(f"{base}/api/tags", timeout=5).json()["models"]]
        except (httpx.HTTPError, KeyError, ValueError):
            problems.append(f"Ollama is not reachable at {base}")
        else:
            if wanted not in names:
                problems.append(f"Ollama does not have {wanted} (ollama pull {wanted})")
    return problems


def run(command: list[str]) -> int:
    return subprocess.run(command, cwd=ROOT).returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--lane", choices=["llama", "frontier", "frontier_large"], required=True)
    parser.add_argument(
        "--first", type=int, help="only the first N cells of the lane, in priority order"
    )
    parser.add_argument(
        "--limit", type=int, help="at most N runs per cell; skips the integrity check"
    )
    parser.add_argument("--dry-run", action="store_true", help="show the order and the checks only")
    args = parser.parse_args()

    cells = lane_cells(expand_cells(load_grid()), args.lane)
    if args.first:
        cells = cells[: args.first]
    print(f"[{stamp()}] lane {args.lane}: {len(cells)} cells in priority order")
    for number, cell in enumerate(cells, start=1):
        print(f"  {number}. {cell.cell_id}")

    # IBAC's intent classifier is always Llama, so any lane with an IBAC cell needs Ollama.
    needs_ollama = args.lane == "llama" or any(c.mediator == "ibac" for c in cells)
    problems = preflight(args.lane, needs_ollama=needs_ollama)
    if problems:
        print("\nnot starting:")
        for item in problems:
            print(f"  - {item}")
        return 2
    print(f"[{stamp()}] checks passed: freeze intact, tree clean, model service ready")
    if args.dry_run:
        return 0

    began = time.monotonic()
    for number, cell in enumerate(cells, start=1):
        print(f"\n[{stamp()}] ({number}/{len(cells)}) {cell.cell_id}", flush=True)
        run_cmd = ["uv", "run", "privilege-drift", "run-cell", cell.cell_id]
        if args.limit:
            run_cmd += ["--limit", str(args.limit)]
        if run(run_cmd) != 0:
            print(f"\n[{stamp()}] STOPPED at {cell.cell_id}: run-cell did not finish cleanly.")
            print("Fix the cause, then run the same command again; finished runs are skipped.")
            return 1
        if (
            not args.limit
            and run(["uv", "run", "privilege-drift", "check-cell", cell.cell_id]) != 0
        ):
            print(f"\n[{stamp()}] STOPPED at {cell.cell_id}: an integrity check failed.")
            return 1
    hours = (time.monotonic() - began) / 3600
    print(f"\n[{stamp()}] lane {args.lane} done: {len(cells)} cells in {hours:.1f} h")
    return 0


if __name__ == "__main__":
    sys.exit(main())
