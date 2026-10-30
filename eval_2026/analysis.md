# 2026 holdout: findings (run once, frozen pipeline)

Settings frozen after the 2023 tuning round: v2 persona recipe, simulation instructions, label sets, scoring rules.
2026 pre-event posts (24 Nov 2024 - 23 Nov 2025) were assigned to the frozen 2023 segments by nearest centroid, so no
one read 2026 data to name clusters. Real side: 387 opinionated reactions from 412 authors, 15-29 Jan 2026.

| | Personas + retrieval (primary) | Personas, no retrieval | Plain prompt | Real |
|---|---|---|---|---|
| Action distance (TVD) | **0.14** | 0.22 | 0.24 | noise floor 0.07 |
| Sentiment distance (TVD) | 0.09 | **0.08** | 0.23 | noise floor 0.06 |
| Theme rank correlation | 0.70 | 0.69 | **0.75** | |
| Leave intent (cancel+switch+downgrade) | **21%** | 12% | 40% | 24% |
| Accept / defend | 19% | 20% | 27% | 30% |

## What held up out of sample

1. **Actions and mood generalise.** The primary method beats the plain prompt on actions (0.14 vs 0.24) and sentiment
   (0.09 vs 0.23); sentiment is close to the noise floor.
2. **Churn talk tracked the real shift.** Real leave intent doubled from 12% (2023) to 24% (2026); the personas moved with
   it (14% to 21%) without retuning. The plain prompt says "~35-40%" both times, whatever the community.
3. **Retrieval mattered this time** (0.14 vs 0.22). The 2025 posts include real reactions to the June 2024 hike, so the
   retrieved evidence carries price behaviour; in 2023 there was no earlier hike to learn from and retrieval added nothing.

## What did not

1. **Plan-cost overshoot (54% vs 11%).** The announcement lists Duo and Family rising by $2, and personas fixate on it;
   real users talked about it far less. Personas react to the stimulus text more literally than people do.
2. **Grievance carry-over persists** (app/UI 34% vs 10%) and **defenders are still short** (19% vs 30%).
3. **Theme ranking is slightly worse than the plain prompt** (0.70 vs 0.75), mostly because of the plan-cost overshoot.
4. **Switch targets:** real switchers favour Apple Music, Tidal, YouTube Music/Premium and Qobuz; personas spread more
   evenly and name Amazon Music, which no real switcher did.

## Data notes

- The real community was primed: the FT reported the plan on ~25 Nov 2025. Personas stop before that report.
- r/spotify activity fell through 2025; most 2026 reaction rows come from r/truespotify (721 of 895 labeled rows).
- Hike threads are detected from all posts incl. short link-post titles (fix applied to both years; it added 21 rows
  in 2023 and no 2023 metric changed).
- Hindsight check: no simulated comment mentions the stock move, the FT report, backlash, or later prices.
