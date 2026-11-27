"""One-off check: which decoding settings does the frontier model accept? (decision D28)

Usage (needs the key in your shell, for example `set -a; source .env; set +a`):

    uv run python scripts/check_frontier_params.py

Sends a handful of tiny requests (a few tokens each, so the cost is negligible) to the frontier
model in `configs/models.yaml`, once with no extra setting and then with temperature, top-p and a
seed, and says which the API accepted. If it accepts temperature and top-p, remove `omit_params`
from the frontier entry so both arms run with identical decoding (the preregistration, decoding
settings); if it rejects them, the departure stays and is reported as a limitation. Run it before
the freeze.
"""

from __future__ import annotations

import os
import sys
from typing import Any

import litellm

from privilege_drift.llm import load_models_config

PROMPT = [{"role": "user", "content": "Reply with exactly: ready"}]


def main() -> int:
    config = load_models_config()
    spec = config.spec("frontier")
    key_name = spec.api_key_env or ""
    api_key = os.environ.get(key_name)
    if not api_key:
        print(f"{key_name} is not set; load your .env first (set -a; source .env; set +a)")
        return 2
    trials: dict[str, dict[str, Any]] = {
        "baseline (no extra setting)": {},
        "temperature": {"temperature": config.sampling.temperature},
        "top_p": {"top_p": config.sampling.top_p},
        "temperature and top_p": {
            "temperature": config.sampling.temperature,
            "top_p": config.sampling.top_p,
        },
        "seed": {"seed": 7},
    }
    accepted: dict[str, bool] = {}
    for name, extra in trials.items():
        try:
            litellm.completion(
                model=spec.litellm_model,
                messages=PROMPT,
                max_tokens=16,
                api_key=api_key,
                timeout=60,
                **extra,
            )
            accepted[name] = True
            print(f"accepted  {name}")
        except Exception as exc:  # report whatever the provider said, briefly
            accepted[name] = False
            print(f"rejected  {name}: {type(exc).__name__}: {str(exc)[:140]}")
    print()
    if not accepted["baseline (no extra setting)"]:
        print("The baseline call failed, so the others say nothing; fix that first (quota? id?).")
        return 1
    if accepted["temperature and top_p"]:
        print("Both accepted: remove `omit_params` from the frontier entry in configs/models.yaml.")
    else:
        print("Not both accepted: keep `omit_params` and report the decoding difference (D28).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
