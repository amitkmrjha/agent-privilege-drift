# D21: How the subset is drawn and how seeds are dealt

- **Status:** Accepted by the author (2026-11-21), as recommended, before the freeze. Earlier status: Proposed (the author confirms before the pre-registration)
- **Date logged:** 2026-11-19
- **Related:** #14, #29, D10

## Decision

- **Subset:** 50 ToolPrivBench scenarios, equal quota per domain (6 each, plus 1 extra for two domains, because 50 = 8 x 6 + 2). The two extra slots and the scenarios inside each domain are chosen by ranking SHA-256 of `(master seed, label, item)` and taking the lowest ranks. No random-number library is used, so the result cannot change with a library version. Master seed: `20261119`.
- **Result (computed, see `prereg/subsets/toolprivbench_50.json`):** Business 7, Coding 7, the other six domains 6 each.
- **Seeds:** one pool of 250 distinct seeds (50 scenarios x 5). Each of the 18 cells deals the whole pool out again in its own hash-ranked order, so within a cell no seed repeats and a scenario's seeds differ between cells (the proposal's "permuted across cells", D10). A 3-seed run uses the first 3 of each scenario's 5 seeds.
- **Binding to the data:** the subset file records the dataset revision and the SHA-256 of `benchmark.jsonl`. `prereg/subsets/HASHES.txt` is in `shasum -a 256` format, so `shasum -c prereg/subsets/HASHES.txt` verifies it. `make subsets-check` regenerates everything and fails if a file differs.

## Rationale

Stratifying by domain is what the plan asks for. Hash ranking gives a draw that nobody can tune (the master seed is the only input) and that stays reproducible across machines and library upgrades.

## Pending / follow-up

- Stratified by domain only. The five risk categories are not balanced; the subset's category counts should be reported in the data chapter.
- "18 cells" is fixed here as an index range. The grid (`configs/grid.yaml`) must number its cells 0 to 17 in a fixed order, and the runner must look seeds up by that index.
- The AgentDojo subset (15 tasks x 15 injections over 5 categories) waits for the AgentDojo loader in #23.
- After the pre-registration tag these files must not change (AGENTS.md rule 3).
