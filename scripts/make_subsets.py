"""Write (or check) the frozen scenario subset and seed schedule under prereg/.

Usage:
    uv run python scripts/make_subsets.py            # write the files
    uv run python scripts/make_subsets.py --check    # fail if the files on disk differ

Needs the ToolPrivBench data (`make data`). Output is a pure function of the master seed and the
data, so running it twice gives identical files; `--check` proves it. After the pre-registration
tag these files must not change (AGENTS.md rule 3).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from privilege_drift.data import DataError
from privilege_drift.data.toolprivbench import DEFAULT_PATH
from privilege_drift.freeze import render_frozen_inputs, render_pilot_inputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--data", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--prereg", type=Path, default=Path("prereg"))
    parser.add_argument("--check", action="store_true", help="compare with disk, write nothing")
    parser.add_argument(
        "--pilot",
        action="store_true",
        help="write the pilot's scenarios and seeds to pilot/ instead (not frozen)",
    )
    args = parser.parse_args()

    try:
        files = (
            render_pilot_inputs(args.data, Path("pilot"), args.prereg)
            if args.pilot
            else render_frozen_inputs(args.data, args.prereg)
        )
    except DataError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    stale = [
        path
        for path, text in files.items()
        if not Path(path).is_file() or Path(path).read_text() != text
    ]
    if args.check:
        for path in stale:
            print(f"DIFFERS  {path}", file=sys.stderr)
        print("subsets and seed schedule match" if not stale else "mismatch")
        return 1 if stale else 0
    for path, text in files.items():
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text)
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
