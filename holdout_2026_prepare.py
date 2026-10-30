#!/usr/bin/env python3
"""
Prepare the Jan 2026 holdout with the FROZEN 2023 pipeline (no retuning).

    python holdout_2026_prepare.py personas      # pre-event rows -> persona_sample_segmented_2026.csv
    python holdout_2026_prepare.py ground-truth   # UNSEALS holdout_2026/post.jsonl -> holdout_2026/ground_truth_core_2026.csv

Persona side, same steps as 2023:
    build_spotify_corpus.clean_rows (phase/role from events.json, hashed authors, keyword flags)
    make_core_files rules (core subreddits, >= 8 words)
    segment_personas.clean + FOCUS filter (>= 15 words, no bots/dupes)
    sample the same size as 2023 (27,686 rows) with the same price-related share (9.4%), even across months
    segment = nearest 2023 segment centroid (MiniLM space). The 2023 segments, names and persona config stay
    frozen, so nobody has to read 2026 data to name clusters.
"""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_spotify_corpus as B
from segment_personas import clean, FOCUS, stratified_sample

B.use_event("2026")
CORE_SUBS = {"spotify", "truespotify"}
N_2023, PRICE_SHARE_2023, SEED = 27686, 0.094, 42


def load(name, label):
    raw = [json.loads(l) for l in open(HERE / "holdout_2026" / f"{name}.jsonl")]
    return pd.DataFrame(B.clean_rows(raw, label))


def personas():
    df = load("pre", "PRE 2026 Arctic Shift r/spotify + r/truespotify (holdout_2026_pull.py)")
    df = df[(df.role == "persona_source") & df.subreddit.isin(CORE_SUBS) & (df.word_count >= 8)]
    df = clean(df, 15)
    df = df[df.text.str.contains(FOCUS)]
    print(f"{len(df):,} cleaned + focused pre-event rows")
    n_price = int(round(N_2023 * PRICE_SHARE_2023))
    price = stratified_sample(df[df.price_related], n_price, SEED)
    rest = stratified_sample(df[~df.price_related], N_2023 - len(price), SEED)
    s = pd.concat([price, rest]).reset_index(drop=True)
    print(f"sampled {len(s):,} rows ({s.price_related.mean():.1%} price-related)")

    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer("all-MiniLM-L6-v2")
    enc = lambda t: m.encode([x[:1200] for x in t], batch_size=128, show_progress_bar=True, normalize_embeddings=True)
    ref = pd.read_csv(HERE / "persona_sample_segmented.csv")
    Zr = enc(ref.text.tolist())
    segs = sorted(ref.segment_id.unique())
    C = np.stack([Zr[ref.segment_id.values == k].mean(0) for k in segs])
    Z = enc(s.text.tolist())
    d = np.linalg.norm(Z[:, None, :] - C[None, :, :], axis=2)
    s["segment_id"] = np.array(segs)[d.argmin(1)]
    s["dist_to_centroid"] = d.min(1)
    s.to_csv(HERE / "persona_sample_segmented_2026.csv", index=False)
    share = s.segment_id.value_counts(normalize=True).sort_index()
    ref_share = ref.segment_id.value_counts(normalize=True).sort_index()
    print(pd.DataFrame({"2023 share": ref_share.round(3), "2026 share": share.round(3)}))


def ground_truth():
    df = load("post", "POST 2026 Arctic Shift r/spotify + r/truespotify (holdout_2026_pull.py)")
    g = df[(df.role == "ground_truth") & (df.word_count >= 8)].copy()
    g["lens"] = "users"
    g.to_csv(HERE / "holdout_2026" / "ground_truth_core_2026.csv", index=False)
    print(f"{len(g):,} post-event rows; price-related {int(g.price_related.sum()):,}")


if __name__ == "__main__":
    {"personas": personas, "ground-truth": ground_truth}[sys.argv[1]]()
