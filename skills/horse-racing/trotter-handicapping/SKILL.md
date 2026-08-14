---
name: trotter-handicapping
description: "Use when analyzing thoroughbred races or DRF Classic PPs. Applies Patrick's race-shape method and logs testable pre-race hypotheses."
version: 1.3.2
author: Patrick Fogarty + Trotter
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [horse-racing, handicapping, drf, past-performances, race-shape, beyer, workouts]
---

# Trotter Handicapping

Use for every race-card or Daily Racing Form PDF analysis. This skill encodes Patrick's current method. It is a living model: explicit Patrick corrections are authoritative; shape-specific strategies remain hypotheses until reviewed across multiple races.

Read before analyzing:

- `references/drf-classic-pp-guide.md`
- `references/race-shape-framework.md`

Use `$TROTTER_WORKSPACE/race-shape-ledger.csv` for pre-race and post-race learning records. If `TROTTER_WORKSPACE` is unset, use the current working directory when it contains the ledger; otherwise fall back to `~/trotter-handicapping`. Keep the ledger outside the installed skill so profile updates never overwrite learning data.

## 1. Extract the race header first

Record, without inference:

- date, track, race number;
- race type and full condition code/text;
- stakes grade, if any;
- purse;
- surface and course;
- distance;
- age and sex restrictions;
- state-bred/other restrictions;
- field size and scratches;
- weather/track condition if known.

Do not rank horses until this is complete. If the PDF text layer is garbled, use PDF extraction/OCR or page images and preserve raw uncertain glyphs.

## 2. Classify the Trotter race shape

Assign one value on each axis from `references/race-shape-framework.md`:

1. condition/class family;
2. surface-distance family;
3. pace pressure;
4. experience/form availability;
5. connection pattern;
6. volatility/data confidence.

State which factors should be emphasized, de-emphasized, or left unresolved. Do not invent numeric weights.

## 3. Build connection profiles

### Trainer and jockey parser

For a line such as:

`Tr: Pletcher Todd A (40 7 5 4 .17) 2026: (345 60 .17)`

extract:

- current meeting: 40 starts, 7 wins, 5 seconds, 4 thirds, .17 win rate;
- current year: 345 starts, 60 wins, .17 win rate.

For jockeys, use the same order when shown.

Apply Patrick's thresholds:

- `.11` or higher = contender-level connection signal;
- `.24` = very good;
- always display starts and period beside the rate;
- record meet and year rates separately;
- `Patrick-recognized` is a distinct yes/no/unknown field, not a replacement for statistics.

Use filtered trainer evidence, when available, to answer a race-specific question: debut runner, surface switch, distance change, layoff, class move, track/circuit shipping, or equipment change. Do not blindly reward a high aggregate percentage. Consider sample size and ROI when shown.

### Owner profile

Until Patrick teaches owner-specific weights, record only:

- Patrick-recognized yes/no/unknown;
- current-meet presence, if shown;
- owner-trainer pairing;
- repeated race type/class placement;
- sample and outcomes when available.

Do not assign an owner bonus without evidence.

## 4. Analyze workouts

Parse each work into:

`date | track | training track | distance | condition | raw time | designation | rank/total`

Rules:

- lower rank numerator is better;
- calculate `top_share = rank / total` with a tool;
- calculate `performance_percentile = 1 - top_share` when useful;
- Patrick's strong-work flag is `top_share <= 0.20`;
- a bullet symbol means best workout of the day at that track and distance;
- `B` commonly denotes breezing; preserve other codes unless the guide verifies them;
- evaluate sequence, spacing, distances, and movement in rank—not one work alone;
- retain raw encoded time symbols unless their fifths mapping is verified from the visual PDF/legend.

Example: `20/100` is top 20% and roughly 80th-percentile performance. `27/28` is near the bottom of that day's comparison group even if the raw time looks acceptable.

### Evidence-based workout learning

A binary strong-work flag is a descriptive feature, not a stand-alone predictive edge. Always compare its prevalence among **all live starters** with its share among winners, second-place finishers, and third-place finishers—card-wide and by exact Trotter shape.

Saratoga 2026-08-01, Races 1–10, provides the first audited baseline:

- strong-work starters: **57/70 (81.4%)**;
- winners with a strong-work flag: **8/10 (80.0%)**, or **-1.4 percentage points** versus starter prevalence;
- second-place horses: **7/10 (70.0%)**, or **-11.4 points**;
- third-place horses: **9/10 (90.0%)**, or **+8.6 points**.

Therefore, the raw `8/10 winners` count did **not** establish a card-wide win edge because strong-work horses were already 81.4% of the fields. Treat workout **recency, concentration, gate designation, surface relevance, sequence quality, and interaction with class/pace/experience** as potentially more informative than the binary flag; these are hypotheses to test, not invented weights.

Preserve exact-shape sample counts. On this baseline, only `C1-DS-P2-E1-K1-V3` repeated, with two races; all other exact shapes had one race. Do not promote a shape-specific workout rule from these samples.

## 5. Apply Patrick's Beyer band

When Beyers are present:

1. Find the field maximum `Bmax` among eligible, visible figures.
2. Set the inclusive band `[Bmax - 10, Bmax]`.
3. For each horse, count figures in the band.
4. Also show eligible starts, recency, surface/distance comparability, and direction of form.
5. Award a speed-consistency advantage to the horse with the strongest repeated presence only if this race shape makes speed evidence reliable.

Never treat missing Beyers as zero. Never mix TimeformUS numbers with Beyers as though they share a scale.

### Patrick-confirmed Beyer and workout refinements

- Use each horse's **six most recent running lines** as the primary Beyer-band window. Keep older/career figures separate as back-class evidence.
- A **current top comparable figure plus a favorable stalking trip** can break a tie over repeated recent consistency immediately below the top/band.
- This tie-break is **conjunctive**: do not invoke it from the top figure alone. If the top-figure horse is a pace-dependent closer rather than a favorable projected stalker, repeated comparable-band presence plus a supported connection/equipment improvement pattern may deserve the higher win-probability ranking.
- Poor workout ranks remain meaningful even for fit, exposed horses; do not dismiss them as maintenance. They are material negatives, not automatic disqualifiers.
- Preserve the official ten-point band. A separate **near-band board flag** for repeated figures within three points below the floor is only a working hypothesis for place/show use until repeated evidence supports it.
- Foreign or missing figures are excluded rather than converted or treated as zero.

### Patrick-confirmed class placement

A move from Saratoga `OC110k/C` into a `$100,000` claiming race is useful class-relief/placement evidence. It can support a rebound when paired with back class, a fitting trip, and race-specific trainer evidence; it does not erase poor current form by itself.

### Calibrated hypotheses from Saratoga 2026-08-07

These are **review flags to test**, not standing predictive rules. Each exact 08/07 shape contributed only one race.

- **Projected-stalk verification:** before using the current-top-plus-stalker conjunction decisively, verify the expected pocket from recent first-call positions, post, and the speed of surrounding runners. If several rivals can displace the horse or force it farther back, mark the trip predicate uncertain.
- **Stale-maximum/weak-field flag:** retain the official ten-point band, but label a stale field maximum explicitly. If no runner has compelling current band evidence, do not let the nominal band create false precision; a recent local near-band route can remain a win/upside candidate rather than board-only.
- **Breakthrough versus repeated class-speed:** when the current top is a one-race breakthrough, compare its repeatability with rivals' repeated graded or course-specific class-speed. A favorable stalking trip supports the breakthrough horse but does not erase the uncertainty.
- **Lightly raced graded upside:** exact-distance success plus concentrated current works and elite race-specific connections can identify development not yet visible in the Beyer band. Record an upside flag; do not automatically promote it over proven current speed.
- **Wire-risk flag:** in a nominally contested sprint, retain a separate wire-risk horse when one forward runner can plausibly clear and has a concentrated relevant work pattern. Compare workout evidence with field prevalence; the binary strong-work flag is not enough by itself.

Keep a count of subsequent supporting and contradicting races before changing contender weights.

### Calibrated checks from Saratoga 2026-08-08

Apply these as **verification checks and review flags**, not fixed numeric weights or universal rules. The card supplied only small exact-shape samples.

- **Projected-trip gate:** a favorable stalking pocket or controlling trip may break a tie only when verified from recent first-call positions, post relationships, all plausible inside/outside speed, jockey usage, and demonstrated ability to relax or sustain the distance. If the trip is uncertain, do not let it decisively displace repeated comparable class-speed. R3, R7, R10, and R14 supplied examples where the assumed trip or controller did not materialize as projected.
- **Reliable-controller test:** before assigning `P1` or elevating likely lone speed, verify (1) recent willingness to lead, (2) no rival with comparable early intent, (3) stamina and rateability at the distance, and (4) that scratches truly improve control. On 2026-08-08 both `C5-TR-P1` primaries missed; exact-family sample=2, so strengthen verification without creating an anti-speed rule.
- **Repeated class-speed protection:** when the opposing primary relies on an isolated maximum or uncertain trip, keep a horse with repeated recent comparable class-speed nearly co-equal in the win tier. Supporting 2026-08-08 examples included San Siro 6/6, Il Siciliano 6/6, Deterministic 5/6, and Sovereignty 4/6; retain recency, surface, distance, class, and actual-trip checks.
- **Development/local-exact-distance upside:** when the field maximum is stale, weak, or unstable, give a clear win-tier upside flag to a lightly raced horse combining current local or exact-distance form, a logical development/class path, relevant trainer evidence, and supporting works/connections. Do not automatically promote it over proven form. R4, R5, and R14 were supporting neighboring examples, not one exact-shape rule.
- **Firster-work quality over raw count:** in debut-heavy races, separately assess gate-work quality, large-sample rank, recency, sequence concentration, distance progression, race-specific debut trainer evidence, and connection balance. A larger number of qualifying works is not automatically superior to fewer highly relevant gate works. The 2026-08-08 `C1-DS-PU-E1-K1-V3` sample was three races and produced mixed transfer; no rule promotion.
- **Poor works remain negative, not a veto:** preserve poor ranks as material contradictory evidence, especially for exposed horses, but test whether repeated class-speed, exact-distance form, surface-change trainer evidence, current local form, a fitting trip, or supported development/equipment evidence can outweigh them. Never erase the poor-work penalty because an individual 0/6 horse won.
- **Foreign-form upside flag:** missing North American Beyers or local works are unknown, not zero. In international turf stakes, flag repeated Group form, suitable distance, equipment changes, connections, and plausible early positioning without converting Timeform to Beyer. Exact-shape supporting sample from R11=1; do not broadly upgrade foreign runners.
- **Safest-show current-readiness check:** historical board reliability must be joined by current readiness, a low-friction projected trip, surface/distance evidence, manageable volatility, and no material health/form contradiction. Do not use lifetime in-the-money percentage alone. Preserve safest show as highest estimated top-three probability, not predicted third.
- **Probability-price separation:** maintain primary, alternative/value, and safest-show roles independently. A winning alternative receives predictive role credit but validates a value thesis only when its locked price requirement was met. Do not force a wager on the primary or retroactively harden approximate price language.

Keep exact-shape and neighboring-shape support/contradiction counts before promoting any of these checks into a standing factor-weight rule.

## 6. Compare factors by shape

Use the starting hypotheses in the race-shape reference. For each factor, label:

- `primary` — likely decision-driving for this shape;
- `supporting` — confirms or weakens;
- `low-information` — missing or unreliable;
- `contradictory` — points against the horse.

Core factors to inspect:

- class/condition fit and purse context;
- pace fit and likely trip;
- Beyer level, consistency, recency, and comparability;
- current form and trouble lines;
- trainer intent/profile;
- jockey current meet/year performance;
- workout readiness;
- surface/distance record and pedigree where relevant;
- owner pattern, only when learned;
- post/field dynamics and scratches.

## 7. Produce the race brief

Use this compact structure:

### Race and shape
One-line race classification plus the six-axis Trotter shape.

### What matters
Primary factors and why this shape elevates them.

### Contenders
A table with: horse, class/form, trainer, jockey, workout signal, Beyer-band count, pace/fit, concerns, confidence.

### Money-horse view

Keep these jobs distinct:

1. **Primary win pick** — most likely winner.
2. **Alternative win/value pick** — second win path or better price; not automatically the safest show horse.
3. **Safest show candidate** — strongest board-probability candidate; may overlap with the win pick.

State a pass condition if evidence is weak or price-sensitive. Odds change value, not the underlying past-performance evidence. Do not chase market steam as proof. Do not guarantee an outcome.

### PDF and full-card table formatting

For every printable race brief or full-card PDF:

- show the official printed morning-line odds immediately after every horse name in the **Primary win**, **Alternative/value**, and **Safest show** cells;
- use the exact format `#3 Gorillaz (ML-5/2)`;
- when a cell contains additional value or secondary horses, print each horse's full name and morning line rather than only the program number, for example `#8 Hemingway (ML-9/2); value #4 With Luck Forward (ML-12/1)`;
- verify every morning line against the supplied DRF or an official live entry source; never infer or invent an odd;
- label `ML` as the printed morning line and keep it distinct from live odds;
- preserve price/pass conditions separately because live odds determine value while the morning line is only the published baseline.

### Scratch discipline

After scratches, rebuild field size, pace, Beyer maximum/band, experience mix, contender interactions, and live roles. Do not merely promote the next-ranked horse. Preserve any original lock unchanged and write a separate scratch addendum when the original analysis was already locked.

### What changes the view
Scratches, surface switch, track bias, live odds, missing pages, or unreadable data.

### Pre-race learning note
Record the shape, predicted key factor, contenders, tosses, and uncertainties before results.

## 8. Review after the result

Hash-lock every pre-race analysis, scratch/odds/method addendum, and post-race review with SHA-256 and verify the sidecar. Never alter a pre-race record after results are known; append a separate review.

Use official charts to verify the live starters, surface, track condition, final odds, exact finish order, payouts, and trip comments. A surface transfer that triggered the published reset condition is `invalidated/no action`, not an ordinary loss. A scratch is excluded or labeled separately rather than graded as a loss.

### Role-separated grading

Grade the locked roles without blending them:

1. primary win-pick wins and ITM results;
2. alternative/value wins and ITM results;
3. safest-show top-three hits and official show payouts;
4. pass races and price-conditioned opinions separately;
5. exacta/trifecta or contender-group coverage only when the order, ticket, or group was explicitly published before the race.

Do not award primary-win credit when an alternative or safest-show horse wins. Do not award winner credit for merely discussing a horse without assigning a published role. Preserve ambiguous price language rather than inventing a minimum after the result.

No wagering return is actual unless a wager was placed. Calculate hypothetical ROI only after declaring the exact stake rule, exclusions, and official payouts; show cost, return, net, and ROI. A transparent baseline is `$2 win on every primary`, with a separate view excluding explicit pass/invalidated races.

### Diagnostic review

Append:

- official order, final odds, payouts, scratches, surface, and source;
- whether each published role succeeded at its assigned job;
- whether the winner fit the Beyer-band, workout, connection, class, pace, local-form, and development/upside hypotheses;
- whether the predicted trip actually occurred, rather than excusing a miss with the pre-race projection;
- shape-classification error vs factor-weight error vs extraction error vs trip/pace vs randomness;
- one candidate adjustment;
- sample count for this exact or neighboring shape.

Promote a hypothesis into a standing rule only after repeated evidence or Patrick's explicit instruction.

## Pitfalls

- DRF says the first trainer/jockey record is for the **current meeting**, not lifetime at the track.
- Purse is a class signal, not a globally comparable class scale; restrictions and meet structure matter.
- A 20/100 workout rank is good because the numerator is low relative to the denominator; 80/100 is not.
- Do not decode garbled month/fifths glyphs from extracted PDF text without visual or source confirmation.
- Do not use a recognizable trainer name as a proxy for the horse's fitness or race fit.
- Do not backfit the shape after seeing the result.
