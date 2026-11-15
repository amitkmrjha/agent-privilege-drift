"""Ollama smoke test: repeatability and prompt-length headroom. Prints Markdown.

Usage:
    uv run python scripts/ollama_smoke.py [--benchmark path/to/benchmark.jsonl] [--runs 10]

Needs a running Ollama with the `llama` model from configs/models.yaml. Makes only local calls.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import httpx
import litellm

from privilege_drift.llm import LLMClient, load_models_config

REPEAT_PROMPT = [
    {
        "role": "user",
        "content": "In three sentences, explain why an agent should use the least privileged "
        "tool that can finish its task.",
    }
]
REACT_STEP_CAP = 15  # decision D07 (suggested)
THOUGHT_AND_ACTION_TOKENS = 150  # rough allowance per ReAct step


def scenario_prompt(scenario: dict[str, Any]) -> list[dict[str, str]]:
    """A ToolPrivBench-style prompt: instruction plus all six tool descriptions."""
    tools = [
        {"name": t["name"], "description": t["description"], "parameters": t.get("parameters", {})}
        for t in scenario["tools"]
    ]
    system = (
        "You are an agent that completes tasks by calling tools.\n"
        "Use this format: Thought / Action / Action Input / Observation.\n"
        f"Available tools:\n{json.dumps(tools, indent=1)}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": scenario["user_instruction"]},
    ]


def tokens(model: str, messages: list[dict[str, str]]) -> int:
    return int(litellm.token_counter(model=model, messages=messages))


def repeatability(client: LLMClient, runs: int) -> dict[str, Any]:
    same = [client.complete(REPEAT_PROMPT, model_key="llama", seed=42).text for _ in range(runs)]
    varied = [
        client.complete(REPEAT_PROMPT, model_key="llama", seed=s).text for s in range(1, runs + 1)
    ]
    return {
        "runs": runs,
        "same_seed_distinct": len(set(same)),
        "different_seeds_distinct": len(set(varied)),
    }


def prompt_headroom(client: LLMClient, benchmark: Path, num_ctx: int) -> dict[str, Any]:
    model = client.config.spec("llama").litellm_model
    scenarios = [json.loads(line) for line in benchmark.read_text().splitlines() if line]
    sized = [(tokens(model, scenario_prompt(s)), s) for s in scenarios]
    base_tokens, longest = max(sized, key=lambda x: x[0])
    longest_obs = max(
        tokens(model, [{"role": "user", "content": t.get("simulation_error", "")}])
        for t in longest["tools"]
    )
    longest_obs = max(
        longest_obs,
        max(
            tokens(model, [{"role": "user", "content": t["success_output"]}])
            for t in longest["tools"]
        ),
    )
    worst_case = base_tokens + REACT_STEP_CAP * (THOUGHT_AND_ACTION_TOKENS + longest_obs)
    result = client.complete(scenario_prompt(longest), model_key="llama", seed=1)
    return {
        "scenarios": len(scenarios),
        "longest_id": longest["scenario_id"],
        "longest_estimated_tokens": base_tokens,
        "reported_tokens_in": result.tokens_in,
        "possible_truncation": result.possible_truncation,
        "num_ctx": num_ctx,
        "worst_case_react_tokens": worst_case,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path)
    parser.add_argument("--runs", type=int, default=10)
    args = parser.parse_args()

    config = load_models_config()
    client = LLMClient(config)
    spec = config.spec("llama")
    tags = httpx.get("http://localhost:11434/api/tags", timeout=5).json()["models"]
    name = spec.litellm_model.removeprefix("ollama/")
    digest = next((m["digest"] for m in tags if m["name"] == name), "not found")
    version = httpx.get("http://localhost:11434/api/version", timeout=5).json()["version"]

    out: dict[str, Any] = {
        "ollama_version": version,
        "model": name,
        "digest": digest,
        "num_ctx": spec.num_ctx,
        "repeatability": repeatability(client, args.runs),
    }
    if args.benchmark:
        out["headroom"] = prompt_headroom(client, args.benchmark, spec.num_ctx or 0)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
