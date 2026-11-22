"""Download ToolPrivBench (CC-BY-4.0) at a pinned revision into data/raw/toolprivbench/.

Usage:
    uv run python scripts/fetch_toolprivbench.py [--dest data/raw/toolprivbench]

Every file is checked against a SHA-256 pinned here, so the experiment cannot silently run on
different data. Files that already match are not downloaded again. Nothing is executed from the
download; it is only parsed as data later.

Data: BAAI/ToolPrivBench, Yang et al., arXiv 2606.20023, licence CC-BY-4.0 (attribute it).
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import httpx

from privilege_drift.data.toolprivbench import BENCHMARK_SHA256, REVISION

REPO = "BAAI/ToolPrivBench"
# Path in the dataset repo -> SHA-256 recorded on 2026-11-19 (benchmark.jsonl equals the
# `source_sha256` in the dataset's own metadata/stats.json). The revision and the benchmark hash
# live in privilege_drift.data.toolprivbench, shared with the frozen subset.
FILES: dict[str, str] = {
    "data/benchmark.jsonl": BENCHMARK_SHA256,
    "metadata/schema.json": "bcf36f0d68262ec6cb3ec98cc67586e4326bc14ed646d117816dae4306fe4961",
    "metadata/stats.json": "42caacba85ddd62d099919d221774068e2e93c6b17eaeaf787d2291a80b08d4d",
    "README.md": "012164c51887bc299ecd7dcd1a085f9dd85783f51641abf07aa2113c3355d203",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(dest: Path, client: httpx.Client) -> int:
    failures = 0
    for name, expected in FILES.items():
        target = dest / name
        if target.is_file() and sha256(target.read_bytes()) == expected:
            print(f"ok       {name} (already present)")
            continue
        url = f"https://huggingface.co/datasets/{REPO}/resolve/{REVISION}/{name}"
        response = client.get(url, follow_redirects=True)
        response.raise_for_status()
        if sha256(response.content) != expected:
            print(f"MISMATCH {name}: download does not match the pinned hash", file=sys.stderr)
            failures += 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(response.content)
        print(f"fetched  {name}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--dest", type=Path, default=Path("data/raw/toolprivbench"))
    args = parser.parse_args()
    with httpx.Client(timeout=60.0) as client:
        return 1 if fetch(args.dest, client) else 0


if __name__ == "__main__":
    raise SystemExit(main())
