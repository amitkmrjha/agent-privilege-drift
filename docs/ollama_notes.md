# Ollama notes

Measured 2026-11-15 with `scripts/ollama_smoke.py` on the development machine (Apple M2, 16 GB RAM, macOS). Re-run the script to refresh these numbers.

## Model and server

| Item | Value |
|---|---|
| Ollama server | 0.40.16 (native install, not Docker; see decision D16) |
| Model tag | `llama3.1:8b-instruct-q4_K_M` |
| Digest (full) | `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e` |
| Digest (short, as shown by `ollama list`) | `46e0c10c039e` |
| Size on disk | 4,920,753,328 bytes (about 4.9 GB), 8.0B parameters, Q4_K_M |
| Model's native context | 131,072 tokens |

Record the full digest and the Ollama version in the pre-registration.

## Context window (`num_ctx`)

`num_ctx` is set explicitly to **8192** in `configs/models.yaml`. Ollama's default is much smaller and it truncates silently.

- **Confirmed it reaches the server:** with `num_ctx: 256`, Ollama's `/api/ps` reported `context_length: 256`.
- **Truncation is not obvious.** A prompt of about 1,000 tokens sent with `num_ctx: 256` was reported as only **130** prompt tokens (not 256), with no error. A check of the form "prompt tokens reached the limit" would miss this.
- **Therefore** every result carries `possible_truncation`, set when the reported prompt size is at or above 98% of `num_ctx`, or below 80% of an independent pre-send estimate (`litellm.token_counter`). On the test above it is `True`; on a normal call it is `False`. A flag means review or exclude the run, not that the call failed. The 80% threshold is a judgement call and has only been checked on these two cases.

## Prompt-length headroom

Checked against all 544 ToolPrivBench scenarios (system text, six tool descriptions, user instruction):

| Measure | Tokens |
|---|---|
| Longest scenario (`HEALTH-TEMP-003`), estimated | 1,289 |
| Same prompt, as reported by Ollama | 1,291 |
| Rough worst case for a 15-step ReAct run (D07) | about 4,440 |
| `num_ctx` | 8,192 |

The longest prompt does not truncate and there is headroom for the step cap. The worst-case figure is an estimate: it assumes 150 tokens of thought and action per step plus the longest tool output in that scenario on every step. AgentDojo prompts are longer; raise `num_ctx` (for example 16,384) for that benchmark and re-run this check.

## Repeatability

Prompt: a three-sentence explanation, `temperature 0.2`, `top_p 0.9`, `max_tokens 2048`, 10 runs each.

| Condition | Distinct outputs out of 10 |
|---|---|
| Same seed (42) | **1** (identical every time) |
| Ten different seeds | **10** |

So a fixed seed reproduces the output exactly on this machine and setup, and the seed does change the output. Limits of this check: one machine, one short prompt, one process, Ollama's default parallelism (the plan recommends `OLLAMA_NUM_PARALLEL=1` for clean latency numbers). It does not show that outputs are identical across machines, Ollama versions or GPU/CPU backends, so do not assume that.

## First-call latency

The first call after the model is not loaded took about 35 seconds (model load). Later calls are much faster. Exclude or flag load time when reporting latency.

## Cache and provenance

- Every `LLMResult` carries `model_fingerprint`, the Ollama digest of the weights that answered. Frontier models have no digest; pin the exact version in `configs/models.yaml`.
- The response cache is off by default and meant for tests. It is keyed by model tag, **digest**, messages, sampling parameters and seed, so re-pointing a tag at new weights is a cache miss.
- Calls **without a seed are never cached** (caching would freeze one random draw), and neither are Ollama calls whose digest cannot be read.
- An unreadable or malformed cache file is treated as a miss and logged; cache writes are atomic.
- Calls have a timeout (`request_timeout_s`, 300 s). A timeout raises `LLMTimeoutError`; any other provider failure raises `LLMCallError`; both derive from `LLMError` and chain the original exception. The client does not retry.
- Logs record sizes, timings and warnings only. Prompts and API keys are never logged (covered by a test).

## Not yet verified

- A real call to the frontier model (`gemini/gemini-2.5-flash`). By design (decision D20) the frontier arm runs after the open-model arm, and no API key has been used. Until then, only the one-line config switch is tested (`tests/test_llm.py`).
