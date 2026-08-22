# Trotter Race-Shape Framework v0.1

For a concise code table, see the [Trotter Complete Race-Shape Key](./complete-race-shape-key.md).

This is a starting taxonomy for learning—not a finished betting system. A race shape is multi-axis. Record all axes before deciding which factors deserve weight.

## Axis 1 — Condition and class family

| Code | Family | Typical questions |
|---|---|---|
| C1 | Maiden special weight, debut-heavy | Which barns can win first out? Are works/pedigree/intent stronger than unavailable speed data? |
| C2 | Maiden special weight, exposed | Who owns the best repeatable figures and form; who can improve? |
| C3 | Maiden claiming | Is there a meaningful class drop, intent signal, or fragile favorite? |
| C4 | Claiming / conditioned claiming / starter | Who fits today's condition, class level, form cycle, and pace? |
| C5 | Allowance / optional claiming / non-winners condition | Who belongs at the condition and can pair class with current form? |
| C6 | Listed or ungraded stakes | Who has stakes-level evidence; is a class riser fast enough? |
| C7 | Grade III | Which horses repeatedly meet the speed/class standard at today's setup? |
| C8 | Grade II | Same, with stronger emphasis on proven class, current form, and pace fit. |
| C9 | Grade I | Deepest class test; demand top-level evidence or a clearly supported improving exception. |
| CX | Other/restricted/special | Preserve full conditions and define the comparison set before weighting. |

Purse is a major class/context signal within the current meet and condition family. Do not compare purse alone across unrestricted, state-bred, restricted, incentive-supported, or different-circuit races.

## Axis 2 — Surface and distance

| Code | Family |
|---|---|
| DS | Dirt sprint |
| DR | Dirt route |
| TS | Turf sprint |
| TR | Turf route |
| AW | All-weather/synthetic |
| OFF | Wet/off main track or moved surface |
| SDX | Unclear/other |

Surface-distance fit controls which prior figures are comparable. A same-scale Beyer can be compared numerically, but repeated performance under today's setup is more informative than an isolated figure under a different setup.

## Axis 3 — Pace pressure

| Code | Shape |
|---|---|
| P1 | Lone/controlling speed |
| P2 | Contested speed / likely pace pressure |
| P3 | Balanced/mixed |
| P4 | Closer-favoring collapse candidate |
| PU | Unknown or insufficient running-style data |

Do not assign pace from names or trainer reputation. Derive it from running lines/pace data and revisit after scratches.

## Axis 4 — Experience and form availability

| Code | Shape |
|---|---|
| E1 | Debut-heavy / little comparable speed data |
| E2 | Lightly raced / rapid improvement possible |
| E3 | Exposed form / stable comparison set |
| E4 | Mixed experience |
| EU | Missing or unreliable data |

## Axis 5 — Connection pattern

| Code | Shape |
|---|---|
| K1 | Multiple elite/high-rate recognizable barns |
| K2 | One dominant connection vs mostly local/unknown rivals |
| K3 | Mixed, no clear connection edge |
| K4 | Local/low-sample/unknown connections dominate |
| KU | Connection data missing |

Recognition is Patrick's learned Saratoga-presence signal. Keep it separate from meet/year win rate and race-specific trainer intent.

## Axis 6 — Volatility and confidence

| Code | Shape |
|---|---|
| V1 | Lower volatility: exposed form, comparable figures, stable surface |
| V2 | Moderate: some unknowns or improving horses |
| V3 | High: many firsters, surface switch, off-track, short samples, or chaotic pace |
| VU | Data incomplete |

## Composite label

Use all six codes, for example:

`C5-DS-P2-E3-K1-V1`

Then write a plain-English sentence. The code is for grouping results; the sentence is for reasoning.

## Starting factor hypotheses by shape

These are observations to test, not numeric weights.

### C1 / E1 — debut-heavy maiden special weight

- likely primary: race-specific trainer debut pattern, work sequence/ranks, pedigree/surface-distance suitability, intent, and live connection pairings;
- supporting: purse/meet caliber and owner-trainer patterns once learned;
- low-information: Beyer consistency when most runners lack figures;
- high volatility by default.

### C2 / E2-E3 — exposed maiden special weight

- likely primary: repeatable comparable Beyers, improvement pattern, trip/comment, pace fit;
- supporting: trainer/jockey and workouts;
- question: is a first-time starter capable of beating the exposed figure standard?

### C3 — maiden claiming

- likely primary: class move, condition fit, current form, trainer intent, pace;
- supporting: Beyer band and works;
- risk: apparent class drops can reflect physical/form concerns.

### C4 — claiming/conditioned claiming/starter

- likely primary: eligibility/condition fit, recent comparable form, pace, class level;
- supporting: trainer placement pattern and jockey;
- risk: overrating a single old top Beyer.

### C5 — allowance/optional claiming

- likely primary: balance of class, comparable Beyer consistency, pace, and current form;
- supporting: trainer/jockey and works;
- question: which runner truly fits today's non-winners condition?

### C6-C9 — stakes and graded stakes

- likely primary: proven/repeatable class-speed standard, current form, distance/surface fit, pace/trip;
- supporting: works and connections, especially for returners or shippers;
- risk: famous connections can be overbet; demand horse-level evidence.

## Workout prevalence standard

For any workout-effectiveness review:

1. define a strong-work horse consistently as having at least one listed work with `rank / field total <= 0.20`;
2. count horses, not individual works;
3. use official live starters after scratches as the baseline denominator;
4. compare baseline prevalence with the strong-work shares of winners, exact second-place finishers, and exact third-place finishers;
5. preserve the exact six-axis shape before any broader surface-distance aggregation;
6. report percentage-point lift as `finisher share - starter prevalence` and retain raw counts;
7. do not infer predictive value from winner prevalence alone when the flag is common throughout the fields.

First audited baseline, Saratoga 2026-08-01 R1–R10: 57/70 starters (81.4%), 8/10 winners (80.0%), 7/10 second-place horses (70.0%), and 9/10 third-place horses (90.0%). This produced no card-wide win lift. Treat recency, concentration, gate designation, surface relevance, and sequence quality as separate interaction hypotheses for future testing.

## Learning standard

For every completed race:

1. preserve the pre-race composite shape;
2. log the predicted primary factor;
3. record top-three finishers and whether selected money horses hit;
4. mark extraction, classification, weighting, trip, or randomness as the main miss type;
5. record one possible adjustment;
6. count the sample for the shape before promoting an adjustment.

Never redefine the pre-race shape after seeing the outcome. If the actual pace differed from the predicted pace, store both `predicted_pace_shape` and `observed_pace_shape`.
