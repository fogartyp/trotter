# DRF Classic Past Performance Guide

## Authoritative sources

1. Daily Racing Form Help, **How to use DRF Past Performances**
   https://help.drf.com/hc/en-us/articles/225544327-How-to-use-DRF-Past-Performances
   Created 2016-08-17; DRF API reports updated 2017-03-03. This is the most useful available official field-by-field guide. Its examples are older, so verify notation changes against the current PDF.

2. Daily Racing Form Help, **How do I learn the meaning of a particular symbol or statistic in DRF Past Performances?**
   https://help.drf.com/hc/en-us/articles/225539687-How-do-I-learn-the-meaning-of-a-particular-symbol-or-statistic-in-DRF-Past-Performances
   Updated 2018-12-07. It directs readers to DRF's usage guide.

3. Daily Racing Form Help, **Working with Past Performance Profiles**
   https://help.drf.com/hc/en-us/articles/225686188-Working-with-Past-Performance-Profiles
   Updated 2020-05-13. Confirms workouts can be shown at the bottom or merged chronologically into running lines.

4. Official DailyRacingForm YouTube, **DRF New Classic Past Performances — Overview**
   https://www.youtube.com/watch?v=ocA-vg63Qck
   Confirms standard views of 12 or 6 running lines and six workouts, with expandable lifetime PPs/workouts.

5. Official DailyRacingForm YouTube, **Using Trainer Stats to Find Winning Horses**
   https://www.youtube.com/watch?v=RS3WvqTZ4DA
   DRF handicappers emphasize using trainer stats to answer intent questions, filtering by race-specific situations, and considering samples and ROI rather than relying on aggregate win rate alone.

6. Official DailyRacingForm YouTube, **DRF Formulator Tip 4 — Merging Workouts**
   https://www.youtube.com/watch?v=XbWvYGCRDNE
   Shows why chronological workout patterns can reveal readiness off a layoff.

7. Official DailyRacingForm YouTube, **DRF Webinar: Beyer Speed Figures**
   https://www.youtube.com/watch?v=6HpBbUe4iHk

## Core race-line fields from DRF's guide

- **Date / race / track:** e.g. race date, race number, and track abbreviation.
- **Track condition:** abbreviated dirt/turf condition.
- **Distance:** an asterisk before the distance means approximate/about.
- **Fractional and final times:** race-leader fractions and winner's final time.
- **Race type / condition:** e.g. `Alw 18700N1X` means an allowance race for non-winners of a race other than maiden or claiming.
- **Claiming class code:** claiming-price range may be shown.
- **Beyer Speed Figure:** a performance number adjusted for race time and track speed, intended to allow comparison across tracks/distances. Do not mix it with other figure scales.
- **Post and calls:** running position and lengths ahead/behind at calls.
- **Finish:** finish position and margin; symbols may denote dead heat.
- **Jockey / weight / equipment / medication:** including apprentice allowance and change indicators.
- **Odds:** an asterisk before odds denotes the betting favorite in the cited guide.
- **Company line / comment / starters:** first three finishers, chart comment, and field size.
- **Career box:** lifetime, current/prior year, track, surface, wet/turf, and distance records; best Beyers by context may appear.
- **Owner / trainer / jockey:** displayed above running lines.

## Trainer and jockey records

DRF's official guide says the record following the jockey's name is for the **current meeting**, followed by the current year; the same applies to the trainer.

Patrick's examples:

`Tr: Pletcher Todd A (40 7 5 4 .17) 2026: (345 60 .17)`

- current meeting: 40 starts, 7 wins, 5 seconds, 4 thirds, .17 win rate;
- 2026: 345 starts, 60 wins, .17 win rate.

`ORTIZ J L (116 28 24 15 .24) 2026: (775 182 .23)`

- current meeting: 116 starts, 28 wins, 24 seconds, 15 thirds, .24 win rate;
- 2026: 775 starts, 182 wins, .23 win rate.

Patrick's current thresholds:

- .11 = contender-level signal;
- .24 = very good;
- always retain starts and period because rates without samples are misleading;
- Patrick-recognized trainer is a separate Saratoga-presence/notable-name signal.

## Workouts

DRF's guide says latest workouts appear under each horse. Classic PPs carry up to six for most horses and up to twelve for first-time starters. The official guide states:

- a bullet symbol denotes the best workout of the day at that track and distance;
- italic numbers such as `1/10` are the workout rank;
- a line such as `4/20` means fourth-fastest of 20 horses at that track and distance that morning.

Patrick's supplied line:

`WORKS: 27Û26 Bel 4f fst :51§ B 27/28 12Û26 Bel tr.t 4f fst :50§ B 40/55 22Þ26 Bel tr.t 4f fst :50© B 20/21 13Þ26 Bel tr.t 4f fst :49 B 51/127 7Þ26 Bel tr.t 4f fst :48¨ B 16/66 22Ü26 Bel tr.t 3f fst :39 B 23/25`

Parse each segment as:

`date | track/training track | distance | condition | raw time | designation | rank/total`

The extracted month glyphs appear to correspond chronologically to July (`Û`), June (`Þ`), and May (`Ü`) in this example, but verify against the visual PDF before normalizing. The symbols after seconds may encode fifths; preserve them raw unless verified.

For `rank/total`:

- `top_share = rank / total`;
- lower is better;
- Patrick flags `top_share <= .20` as strong;
- `20/100` is top 20%, or roughly 80th-percentile performance relative to the peer group;
- compare patterns across recent works, not just one rank.

## DRF race-shape symbols vs Trotter shapes

DRF has separate `C` and `S` pace/race-shape symbols. Official help article:
https://help.drf.com/hc/en-us/articles/360001488568-What-Are-The-C-and-S-Pace-Symbols-In-the-Past-Performances

Do not assume their exact meaning from the letters alone; consult the linked current explanation when those symbols appear. Trotter's own multi-axis race-shape classification is a separate analytical framework.

## Extraction rule

A PDF text layer can turn month or fractional-time symbols into characters such as `Û`, `Þ`, `Ü`, `§`, `©`, or `¨`. Keep both:

- `raw_value` exactly as extracted;
- `normalized_value` only when verified visually or by an official legend.

Never let an encoding guess drive a selection.
