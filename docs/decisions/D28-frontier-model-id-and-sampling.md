# D28: Frontier model id, and sampling settings the frontier API rejects

- **Status:** Accepted by the author (2026-11-21), as recommended, before the freeze. Earlier status: Proposed (the model id is provisional until issue #28 chooses the frontier model)
- **Date logged:** 2026-11-20
- **Related:** #28, #24, D09, D20

## Decision

1. The frontier entry in `configs/models.yaml` is `gemini/gemini-3.5-flash-lite` for now. It is a pinned id: no `-latest` alias and no `-preview` name, because those can change or be retired.
2. A model entry may list `omit_params` (only `temperature` and `top_p` are allowed). The client leaves those settings out of that model's requests. The frontier entry uses this because the first Gemini model tried (`gemini-3.8-flash`) rejected both with `UnsupportedParamsError`.
3. Whether `gemini-3.5-flash-lite` also needs `omit_params` has **not** been checked. If it accepts `temperature` and `top_p`, remove the setting so both arms use identical decoding.

## Rationale

On 2026-11-20 the planned `gemini-2.5-flash` returned a 404 ("no longer available to new users"), and `gemini-3.8-flash` returned 503 "high demand", so the small frontier test used a flash-lite model. Rule 4 in AGENTS.md says sampling constants must be identical across arms. Where the provider forbids a setting, the departure is made explicit in config, not hidden by a global "drop unsupported parameters" switch.

## Consequences

- If `omit_params` stays in force for the experiment, the Llama arm (temperature 0.2, top-p 0.9) and the frontier arm (provider defaults) differ in decoding. This must be reported as a limitation of RQ1.
- Gemini runs record no model fingerprint (only Ollama exposes a digest), so the model id in `configs/models.yaml` and the git commit in each manifest are the only record of which model was used. Write the exact id in the pre-registration and the thesis.
- `configs/models.yaml` is not part of the manifest's `config_hash` (only the grid is). Not changed here; worth deciding in #26.

## Pending / follow-up

Owner: #28 (choose the model), #26 (settle this decision). Needs the supervisor's agreement that a flash-lite model is an acceptable "frontier baseline", or a different model.

## Accepted 2026-11-21

Decision: the frontier model is pinned as `gemini/gemini-3.5-flash-lite`. Its decoding: `omit_params` (temperature, top-p) stays until `scripts/check_frontier_params.py` shows whether this model accepts them; if it does, remove `omit_params` before the freeze so both arms use identical decoding.
