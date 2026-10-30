#!/usr/bin/env python3
"""
Turn the raw merged corpus (spotify_2023_corpus.csv) into analysis-ready files.
Run from the folder that contains the corpus:   python make_core_files.py            (July 2023)
                                                python make_core_files.py --event 2026   (Jan 2026 holdout)

  spotify_persona_core.csv       Task 3-4 input: on-topic pre-event rows only
  spotify_ground_truth_core.csv  Task 6 input: on-topic post-event rows, with a `lens` column
"""
import sys
import pandas as pd
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVENT = sys.argv[sys.argv.index("--event") + 1] if "--event" in sys.argv else "2023"
SUF = "" if EVENT == "2023" else f"_{EVENT}"      # 2023 keeps its original file names
df = pd.read_csv(HERE / f"spotify_{EVENT}_corpus.csv")

CORE_SUBS   = {"spotify", "truespotify"}                       # the community we are simulating
USER_SUBS   = CORE_SUBS | {"AppleMusic", "entertainment", "malaysia", "audiophile"}
INVESTOR    = {"wallstreetbets", "stocks", "investing", "Superstonk", "plutus"}
BOT_SUBS    = {"AutoNewspaper", "opscanbot"}
NOISE_SUBS  = {"BestofRedditorUpdates", "AmItheAsshole", "HFY", "antiwork", "assholedesign",
               "MaliciousCompliance", "LifeProTips", "TrueOffMyChest", "meirl", "memes", "dataisbeautiful"}

# ---------- persona source (pre-event) ----------
P = df[df.role == "persona_source"].copy()
P["on_topic"] = P.subreddit.isin(CORE_SUBS) | (P.mentions_spotify & ~P.subreddit.isin(NOISE_SUBS | INVESTOR))
P = P[P.on_topic & (P.word_count >= 8)].drop(columns=["on_topic"])
P.to_csv(HERE / f"spotify_persona_core{SUF}.csv", index=False)

# ---------- ground truth (post-event) ----------
G = df[df.role == "ground_truth"].copy()
G = G[~G.subreddit.isin(BOT_SUBS)]
def lens(r):
    if r.subreddit in INVESTOR:                      return "investors"
    if r.subreddit in NOISE_SUBS and not r.mentions_spotify: return "off_topic"
    if r.subreddit in USER_SUBS or r.mentions_spotify:       return "users"
    return "off_topic"
G["lens"] = G.apply(lens, axis=1)
G = G[(G.lens != "off_topic") & (G.word_count >= 8)]
G.to_csv(HERE / f"spotify_ground_truth_core{SUF}.csv", index=False)

print("persona core :", len(P), "rows |", P.subreddit.nunique(), "subreddits | posts", (P.kind=='post').sum(), "| comments", (P.kind=='comment').sum())
print("ground truth :", len(G), "rows | by lens:", G.lens.value_counts().to_dict())
print("ground truth users lens, price-related:", int(((G.lens=='users') & G.price_related).sum()))
