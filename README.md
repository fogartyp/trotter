# Trotter

[![validate](https://github.com/fogartyp/trotter/actions/workflows/validate.yml/badge.svg)](https://github.com/fogartyp/trotter/actions/workflows/validate.yml)
[![skills.sh](https://skills.sh/b/fogartyp/trotter)](https://skills.sh/fogartyp/trotter)

Trotter is Patrick Fogarty's evidence-first thoroughbred handicapping profile for [Hermes Agent](https://hermes-agent.nousresearch.com/docs). It packages the profile identity, the reusable `trotter-handicapping` skill, its DRF/race-shape references, and a public archive of daily picks.

The method is deliberately auditable: classify the race before weighting evidence, keep connection samples visible, compute workout ranks, use an inclusive ten-point Beyer band, distinguish the safest show candidate from the projected winner, and lock pre-race opinions before results.

> [!IMPORTANT]
> Horse-racing analysis is uncertain. Nothing here guarantees a result or profit, and no file in this repository records or submits a wager.

## Install the complete Hermes profile

Hermes Agent 0.20.0 or newer can install this repository as a profile distribution:

```bash
hermes profile install https://github.com/fogartyp/trotter.git --alias
hermes profile use trotter
```

The install owns only `SOUL.md`, `profile.yaml`, `skills/`, and `distribution.yaml`. Local credentials, configuration, memories, sessions, race ledgers, and workspace files remain user-owned and are not replaced by updates.

Update later with:

```bash
hermes profile update trotter
```

Inspect the installed distribution with:

```bash
hermes profile info trotter
```

## Install only the skill

For Codex and other Agent Skills-compatible harnesses:

```bash
npx skills@latest add fogartyp/trotter
```

The installable skill lives at [`skills/horse-racing/trotter-handicapping`](./skills/horse-racing/trotter-handicapping/SKILL.md).

## Repository map

```text
.
├── SOUL.md                       # Trotter's stable identity and guardrails
├── distribution.yaml            # Hermes profile-distribution manifest
├── profile.yaml                 # Short profile description
├── skills/horse-racing/
│   └── trotter-handicapping/     # Skill, references, agent metadata
├── picks/
│   ├── README.md                 # Chronological index
│   └── full-card/                # Daily full-card picks and SHA-256 sidecars
└── scripts/
    ├── sync_from_local.py        # Allowlisted local-to-repo sync
    └── validate.py               # Structure, integrity, and secret checks
```

## Daily picks

The chronological archive is in [`picks/`](./picks/README.md). Each published card keeps its original integrity sidecar, with verification paths documented in that directory. `ML` always means the printed morning line, not live odds. Late analyses, pass conditions, surface-reset conditions, and unresolved scratch status stay visible rather than being rewritten after the fact.

Daily Racing Form PDFs, attachments, screenshots, official chart PDFs, and bulk extracted PP text are intentionally excluded. The archive publishes Trotter's original analysis plus limited cited race-form facts such as horse names, conditions, figures, workout ranks, and connection records—not the underlying copyrighted race forms. Third-party data remains subject to its owner's terms.

## Maintaining the package

From a local Trotter setup:

```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/sync_from_local.py
npm test
```

The sync is allowlist-only. It copies:

- `SOUL.md` and `profile.yaml` from `$HERMES_HOME`;
- the custom `trotter-handicapping` skill and Markdown references;
- `*-full-card.md` picks and their SHA-256 sidecars from `$TROTTER_WORKSPACE/full-card`.

`skills/horse-racing/trotter-handicapping/agents/openai.yaml` is repository-maintained UI metadata and is intentionally preserved rather than copied from the local profile. The sync rejects source symlinks, detects stale generated output, and never copies `.env`, `config.yaml`, OAuth material, memories, databases, logs, sessions, caches, attachments, or source DRF PDFs. Use `python3 scripts/sync_from_local.py --check` to detect drift without writing.

## Method overview

1. Record race context and class.
2. Parse trainer and jockey meet/year records with sample sizes.
3. Evaluate workout sequences; `rank / total <= .20` is descriptive strong-work evidence, not a stand-alone edge.
4. Compute the field's inclusive ten-point Beyer band from visible comparable figures.
5. Classify the six-axis Trotter race shape before deciding which factors matter.
6. Publish primary win, alternative/value, and safest-show roles separately.
7. Hash-lock pre-race work; append results in a separate review without hindsight edits.

See the full [`trotter-handicapping` skill](./skills/horse-racing/trotter-handicapping/SKILL.md) and its [`race-shape framework`](./skills/horse-racing/trotter-handicapping/references/race-shape-framework.md).

## License

The profile, skills, scripts, and original analysis in this repository are available under the [MIT License](./LICENSE). Third-party racing data and linked source material remain subject to their respective owners' terms.
