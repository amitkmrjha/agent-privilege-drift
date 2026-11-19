# D22: How the failure draws are made

- **Status:** Proposed (departs from the wording of issue #16)
- **Date logged:** 2026-11-19
- **Related:** #16, #21, D21

## Decision

Draw number `n` of a run is SHA-256 of `master seed | cell index | scenario id | seed index | n`, read as a number in [0, 1). The call fails when the draw is below p. The issue text and the plan say to seed `numpy.random.SeedSequence([master, cell_idx, scenario_idx, seed_idx])`; this does the same job without a random-number library. It uses the scenario id, not its position in the list, so the draws do not move if the subset changes.

## Rationale

- **No library dependence.** numpy does not promise that a generator's stream stays the same across versions. This method gives the same draws on any machine, forever, which a pre-registered experiment needs.
- **Resumable.** The draw depends only on the call number, not on hidden generator state. A run that was stopped continues from call `n` with exactly the draws it would have had (`start_index`).
- **Consistent** with the hash-ranked choices in D21.
- Tests check the rate (within four standard deviations at p = 0.3 and 0.6), p = 0 never injects, p = 1 always injects, same key gives the same sequence, any changed key part changes it, and two hits in a row occur at about p squared.

## Pending / follow-up

If the author prefers numpy's `SeedSequence` as written in the plan, only `unit_draw` changes. Settle this in #26, before the pre-registration, since the choice changes which calls fail.
