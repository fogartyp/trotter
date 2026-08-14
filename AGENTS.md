# Repository instructions

This repository publishes Trotter's Hermes profile, Trotter-owned handicapping skills, and immutable daily-pick artifacts.

## Before changing handicapping content

- Read `skills/horse-racing/trotter-handicapping/SKILL.md` and both linked references.
- Keep source facts, Patrick rules, Trotter inferences, and unknowns distinct.
- Never invent figures, works, conditions, scratches, results, odds, or connection statistics.
- Preserve primary win, alternative/value, and safest-show as separate roles.
- Never alter a pre-race pick after results are known; add a separate review instead.

## Packaging rules

- `SOUL.md`, `profile.yaml`, and the packaged skill come from the active Trotter profile.
- Daily picks come only from `*-full-card.md` and matching SHA-256 sidecars.
- Do not commit credentials, `config.yaml`, memories, state databases, logs, sessions, attachments, DRF PDFs, chart PDFs, screenshots, or extracted PP text.
- Run `python3 scripts/sync_from_local.py --check` when local source trees are available.
- Run `python3 scripts/validate.py` before every commit.
