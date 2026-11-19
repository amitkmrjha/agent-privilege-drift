"""How often does the IBAC classifier recover each scenario's true domain? Prints JSON.

Usage:
    uv run python scripts/classifier_accuracy.py [--limit N]

Uses the 50 frozen scenarios and the local Llama (needs a running Ollama and `make data`). It
makes at most 2 short local calls per scenario, no paid calls. The result belongs in docs/pilot.md.
"""

from __future__ import annotations

import argparse
import sys

from privilege_drift.data import DataError
from privilege_drift.llm import LLMClient, LLMError, load_models_config
from privilege_drift.mediators import IntentClassifier, default_taxonomy, evaluate_classifier
from privilege_drift.runner import load_grid, load_plan_inputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--limit", type=int, default=None, help="only the first N scenarios")
    args = parser.parse_args()
    try:
        inputs = load_plan_inputs(load_grid())
        scenarios = [inputs.scenarios[i] for i in inputs.scenario_ids][: args.limit]
        classifier = IntentClassifier(LLMClient(load_models_config()), default_taxonomy())
        report = evaluate_classifier(classifier, scenarios)
    except (DataError, LLMError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(report.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
