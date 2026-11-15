# D17: No automated dependency updates

- **Status:** Accepted (done)
- **Date logged:** 2026-11-15
- **Related:** PR #50

## Decision

No `dependabot.yml`. Enable GitHub security alerts in repo settings instead.

## Rationale

An automatic bump after the code freeze would change `uv.lock`, which the pre-registration pins and hashes.

## Pending / follow-up

Revisit after the study is released.
