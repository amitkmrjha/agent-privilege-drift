"""Prepare, verify and tag the pre-registration freeze (issue #30).

    uv run python scripts/freeze.py --check     what is blocking the freeze (changes nothing)
    uv run python scripts/freeze.py --prepare   on a branch: write prereg/freeze_record.json and
                                                fill section 11 of the pre-registration
    uv run python scripts/freeze.py --verify    does the tree still match the record?
                                                (also `make freeze-check`)
    uv run python scripts/freeze.py --tag [--push]
                                                on main, after the prepare PR is merged:
                                                create the annotated tag (and push it)

The order matters because the freeze must not be pushed straight to main: --prepare runs on a
branch and its commit goes through a pull request; --tag then verifies that nothing has moved
since and tags the merged commit. The tag must be on the remote before any full run.

The freeze refuses to proceed while the pre-registration still has a [CONFIRM] or [FILL] marker, the
frozen subset does not match its regeneration, or (for --prepare and --tag) the tree is not clean.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from privilege_drift.data.toolprivbench import BENCHMARK_SHA256
from privilege_drift.freeze_record import (
    RECORD_NAME,
    FreezeRecord,
    build_record,
    compare,
    open_markers,
    read_record,
    with_freeze_section,
    write_record,
)
from privilege_drift.llm import load_models_config
from privilege_drift.runner import load_grid

ROOT = Path.cwd()
PREREG = ROOT / "prereg" / "preregistration.md"
RECORD = ROOT / "prereg" / RECORD_NAME
DEFAULT_TAG = "exp-v2"


def git(*args: str) -> str:
    done = subprocess.run(["git", *args], capture_output=True, text=True, check=True, cwd=ROOT)
    return done.stdout.strip()


def run(*command: str) -> bool:
    return subprocess.run(command, cwd=ROOT).returncode == 0


def blockers(*, need_clean_tree: bool) -> list[str]:
    """Everything that stops the freeze, as short sentences. Empty means ready."""
    found: list[str] = []
    for number, line in open_markers(PREREG.read_text()):
        found.append(f"pre-registration line {number} is still open: {line[:90]}")
    if need_clean_tree and git("status", "--porcelain"):
        found.append("the working tree has uncommitted changes")
    if not run("uv", "run", "python", "scripts/make_subsets.py", "--check"):
        found.append("the frozen subset or seed schedule differs from its regeneration")
    return found


def settings() -> dict[str, object]:
    grid = load_grid()
    return {
        "seeds_per_scenario": grid.seeds_per_scenario,
        "max_steps": grid.max_steps,
        "window_k": grid.window_k,
        "frontier_model": load_models_config().spec("frontier").litellm_model,
        "frontier_omit_params": load_models_config().spec("frontier").omit_params,
        "frontier_large_model": load_models_config().spec("frontier_large").litellm_model,
    }


def make_record(tag: str) -> FreezeRecord:
    s = settings()
    return build_record(
        ROOT,
        tag=tag,
        code_commit=git("rev-parse", "HEAD"),
        created_utc=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        prereg_text=PREREG.read_text(),
        benchmark_sha256=BENCHMARK_SHA256,
        frontier_model=str(s["frontier_model"]),
        frontier_large_model=str(s["frontier_large_model"]),
        seeds_per_scenario=int(str(s["seeds_per_scenario"])),
        max_steps=int(str(s["max_steps"])),
        window_k=int(str(s["window_k"])),
    )


def cmd_check(tag: str) -> int:
    print("settings that would be frozen:")
    for key, value in settings().items():
        print(f"  {key}: {value}")
    found = blockers(need_clean_tree=False)
    if not found:
        print("\nready: nothing blocks the freeze. Next: --prepare on a branch.")
        return 0
    print(f"\n{len(found)} thing(s) block the freeze of {tag}:")
    for item in found:
        print(f"  - {item}")
    return 1


def cmd_prepare(tag: str, *, skip_checks: bool) -> int:
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if branch in ("main", "master"):
        print("error: run --prepare on a branch (pushing to main is not allowed); then open a PR")
        return 2
    found = blockers(need_clean_tree=True)
    if found:
        print("not ready:")
        for item in found:
            print(f"  - {item}")
        return 1
    if not skip_checks and not run("make", "check"):
        print("error: `make check` failed; fix it before the freeze")
        return 1
    record = make_record(tag)
    write_record(record, RECORD)
    PREREG.write_text(with_freeze_section(PREREG.read_text(), record))
    print(f"wrote {RECORD.relative_to(ROOT)} and filled section 11 of the pre-registration")
    print(f"run files digest {record.run_digest}")
    print(f"code commit {record.code_commit}")
    print("next: commit both files, open a PR, merge it, then on main: --tag --push")
    return 0


def cmd_verify() -> int:
    if not RECORD.is_file():
        print("not frozen yet: no freeze record")
        return 0
    drift = compare(ROOT, read_record(RECORD), PREREG.read_text())
    for label, files in (
        ("changed", drift.run_changed),
        ("added", drift.run_added),
        ("removed", drift.run_removed),
    ):
        for path in files:
            print(f"DEVIATION: run file {label}: {path} (log it in docs/deviations.md)")
    if drift.prereg_changed:
        print("DEVIATION: the registered text of the pre-registration changed")
    for path in drift.analysis_changed:
        print(f"note: analysis file changed since the freeze: {path} (mention it in the log)")
    if not drift.experiment_changed:
        print("the experiment still matches the freeze record")
    return 1 if drift.experiment_changed else 0


def cmd_tag(tag: str, *, push: bool) -> int:
    if git("rev-parse", "--abbrev-ref", "HEAD") != "main":
        print("error: tag from main, after the prepare PR is merged")
        return 2
    git("fetch", "origin")
    if git("rev-list", "HEAD..origin/main"):
        print("error: main is behind origin/main; pull first")
        return 2
    if not RECORD.is_file():
        print("error: no freeze record; run --prepare on a branch and merge it first")
        return 2
    found = blockers(need_clean_tree=True)
    if found:
        print("not ready:")
        for item in found:
            print(f"  - {item}")
        return 1
    record = read_record(RECORD)
    drift = compare(ROOT, record, PREREG.read_text())
    if drift.experiment_changed:
        print("error: files changed since the record was made; run --verify to see which")
        return 1
    if git("tag", "--list", tag):
        print(f"error: tag {tag} already exists")
        return 2
    git(
        "tag",
        "-a",
        tag,
        "-m",
        f"Pre-registration freeze {tag}: run digest {record.run_digest}",
    )
    print(f"created tag {tag} at {git('rev-parse', 'HEAD')}")
    if push:
        git("push", "origin", tag)
        print(f"pushed {tag}: the freeze is on the remote, full runs may start")
    else:
        print(f"not pushed yet: `git push origin {tag}` before any full run")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--verify", action="store_true")
    mode.add_argument("--tag-now", "--tag", dest="tag_now", action="store_true")
    parser.add_argument("--name", default=DEFAULT_TAG, help="tag name (default exp-v2)")
    parser.add_argument("--push", action="store_true", help="with --tag: push the tag")
    parser.add_argument(
        "--skip-checks", action="store_true", help="with --prepare: skip make check"
    )
    args = parser.parse_args()
    if args.check:
        return cmd_check(args.name)
    if args.prepare:
        return cmd_prepare(args.name, skip_checks=args.skip_checks)
    if args.verify:
        return cmd_verify()
    return cmd_tag(args.name, push=args.push)


if __name__ == "__main__":
    sys.exit(main())
