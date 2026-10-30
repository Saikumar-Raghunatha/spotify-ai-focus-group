# Spotify AI Focus Group: Can LLM personas predict a price-hike backlash?

Final project for **Analytics for Unstructured Data** (MS Business Analytics, The University of Texas at Austin, Fall 2026). Group project.

We built an AI "focus group" of 28 personas from what r/spotify and r/truespotify users wrote **before** a price increase, showed them the announcement, and compared their reactions with what the real community posted afterward. We tuned once on the July 2023 US hike ($9.99 to $10.99), froze everything, and ran a one-shot holdout on the January 2026 hike ($11.99 to $12.99).

## Headline results

| Measure | 2023 personas | 2023 plain prompt | 2023 real | 2026 personas | 2026 plain prompt | 2026 real |
|---|---|---|---|---|---|---|
| Say they'll leave (cancel / switch / downgrade) | 14% | 35% | 12% | 21% | 40% | 24% |
| Defend the price | 32% | 28% | 40% | 19% | 27% | 30% |
| Action distance to real (TVD, 0 = identical) | 0.11 | 0.30 | floor 0.06 | 0.14 | 0.24 | floor 0.07 |
| Sentiment distance to real (TVD) | 0.20 | 0.19 | floor 0.05 | 0.09 | 0.23 | floor 0.06 |
| Theme rank correlation with real | 0.88 | 0.69 | | 0.70 | 0.75 | |

"Floor" = how far two random halves of the real data differ, the best any simulation can reach. Full write-ups: `eval_2023/report.md`, `eval_2026/report.md`.

## Method in brief

1. **Data:** ~690K public Reddit posts and comments pulled from the Arctic Shift archive; usernames replaced by a salted one-way hash.
2. **Segmentation:** MiniLM sentence embeddings + k-means (k = 6, chosen by silhouette score).
3. **Personas:** 28 per event, each written by Claude Haiku from its own real pre-event posts, with retrieval (cosine search) over only its own post history.
4. **Simulation:** three conditions (personas + retrieval, personas without retrieval, plain prompt), 5 runs each, structured JSON answers.
5. **Evaluation:** real post-announcement comments labeled with the same actions, sentiments and themes; compared with total variation distance, Spearman rank correlation and leave/defend rates against a noise floor.

## What is not in this repository

Raw Reddit data, the cleaned corpora and the embedding files (~950 MB) are left out because of size. The pull and preparation scripts below rebuild them.

---

## Working notes (original project README)


**Idea:** build an AI copy of the r/spotify community from posts written BEFORE the 24 Jul 2023 US price hike
($9.99 to $10.99), show it the announcement, and test whether its reaction matches what the real community said afterward.

## Pipeline, in order

| Task | What | Run | Output |
|---|---|---|---|
| 1-2 | Pull Reddit data (pre-event personas, post-event ground truth) | `python arctic_shift_pull.py --test` then `python arctic_shift_pull.py` | `arctic_spotify_pre.jsonl`, `arctic_spotify_post.jsonl` |
| 1-2 | Merge with the Apify scrapes, label every row | `python build_spotify_corpus.py` (set `APIFY_TOKEN` to include the Apify datasets) | `spotify_2023_corpus.csv/.jsonl`, `corpus_summary.json` |
| 1-2 | Filter to on-topic rows | `python make_core_files.py` | `spotify_persona_core.csv`, `spotify_ground_truth_core.csv` |
| 3 | Segment the community | `python segment_personas.py --input spotify_persona_core.csv --focus --price-boost 4000 --sample 20000 --outdir task3_output_final` | `segment_profiles.md`, `persona_sample_segmented.csv` |
| 4 | Build persona agents + retrieval index | `python build_personas.py --input task3_output_final/persona_sample_segmented.csv` (needs `ANTHROPIC_API_KEY`) | `task4_output/` (`personas.json`, `persona_cards.md`, `index/`) |
| 5 | Simulate the reaction + baselines | not written yet | |
| 6 | Label real reaction, score, failure analysis, slides | not written yet | |

## Key columns in the corpus
| column | meaning |
|---|---|
| `phase` | `pre` (2022-07-21 to 2023-07-20), `leak_gap` (07-21 to 07-23, news leaked), `post` (07-24 to 08-07), `out_of_window` |
| `role` | `persona_source` (Tasks 3-4), `ground_truth` (Task 6), `excluded` |
| `text` | post title + body, or comment body |
| `mentions_spotify`, `price_related` | cheap keyword flags to filter noise |
| `author_hash` | hashed username (real usernames are not stored) |
| `lens` (ground-truth file only) | `users` = score against this; `investors` = a separate lens |

## Rules for everyone
1. Personas may only use `role == persona_source` rows.
2. `role == ground_truth` rows must NEVER reach the personas. That is what keeps the back-test honest.
3. Phase comes from each row's own timestamp, so a late comment on an old post is excluded automatically.
4. Never commit API keys or tokens. Set them as environment variables.
5. Big CSVs: use Python/pandas, not Excel.

## Holdout event: Jan 2026 hike (second test, run ONCE, no retuning)
Spotify US hike announced 15 Jan 2026 ($11.99 to $12.99). Dates live in `events.json`. Pull it the same way as 2023, with `--event 2026`:
```
python arctic_shift_pull.py --event 2026 --test     # check Arctic Shift has 2026 data
python arctic_shift_pull.py --event 2026            # writes arctic_spotify_2026_pre.jsonl / _post.jsonl
python build_spotify_corpus.py --event 2026         # writes spotify_2026_corpus.csv, corpus_summary_2026.json
python make_core_files.py --event 2026              # writes spotify_persona_core_2026.csv, spotify_ground_truth_core_2026.csv
```
2023 files are never overwritten (2026 outputs carry `2026` in the name).
- **Sealed rule:** the 2026 pre-event data is used later to rebuild personas with the SAME pipeline and settings (no retuning). The 2026 POST-event file and ground-truth core stay unopened until the 2023 pipeline is frozen.
- **Cutoff = 2025-11-24, not the announcement date.** The Financial Times reported on ~25 Nov 2025 that Spotify would raise US prices in Q1 2026, and online reaction to that report was strongly negative. So personas use posts from 2024-11-24 to 2025-11-24 (still a full year), everything from 2025-11-24 to 2026-01-14 is excluded from BOTH sides, and ground truth is 15-30 Jan 2026 (the official announcement).
- **Known caveat:** the real community was already primed by the November report, but the personas are not. Expect a more muted real reaction than in 2023, and say so in the failure analysis.
- `holdout_2026_run_inputs.json` is only a backup (Apify) if Arctic Shift has no 2026 data. No need to share it.

## Known limits (say these in the report)
- Reddit only, and r/spotify and r/truespotify skew toward people who post.
- Pre-event talk was mostly about the UI redesign, not price, so personas may lean angrier than the real reaction.
- Post-event reaction is front-loaded: most of it lands in the first 2-3 days.
- LLMs may already "know" how the 2023 hike played out, so check simulation outputs for hindsight.

## Tasks 4-6 (built Oct 2026, LLM steps run as Claude Code Haiku subagents, no API key)
| Step | Run | Output |
|---|---|---|
| 4 Personas | `python make_personas.py --config persona_config_v2.json --outdir personas_v2` → agents draft `drafts/<id>.json` → `--finalize` | `personas_v2/` (28 personas, cards, local vector index) |
| 5 Simulation | `python simulate.py prep --tag v2` → one agent per brief → `python simulate.py collect --tag v2` | `sim_2023_v2/results.csv` (v1 untuned + plain baseline in `sim_2023/`) |
| 6 Labels | `python evaluate.py prep-labels` → agents label briefs → `python evaluate.py collect-labels` | `eval_2023/real_labels.csv`, `handcheck_100.csv` |
| 6 Score | `python evaluate.py score --event 2023` | `eval_2023/report.md`, `analysis.md`, `fig_*.png` |
| Holdout | `holdout_2026_pull.py` → `holdout_2026_prepare.py personas` → same steps with `--event 2026` / `personas_2026` | `eval_2026/` |
| Deliverables | `python export_results.py && python build_demo.py`; deck: `node deliverables/build_deck.js results.json deck.pptx` | `deliverables/` |
Frozen after the 2023 tuning round: `persona_config_v2.json`, simulation and labeling instructions, scoring rules.
