#!/usr/bin/env python3
"""
TASK 3: find the community segments inside the pre-event Spotify data.

Reads  spotify_persona_core.csv  (persona_source rows only), cleans and samples it,
embeds the text, clusters it into 6-8 concern-based segments, and writes profiles
the team can read and name.

Setup (once):   pip install pandas numpy scikit-learn sentence-transformers
Run:            python segment_personas.py --input spotify_persona_core.csv
Quick test:     python segment_personas.py --input spotify_persona_core.csv --backend tfidf --sample 3000

Outputs (in ./task3_output):
    persona_sample_segmented.csv   every sampled row + its segment_id (input for Task 4)
    segment_profiles.json          machine-readable profiles
    segment_profiles.md            human-readable: keywords, signal rates, example posts -> NAME THE SEGMENTS
"""
import argparse, json, re, sys, warnings
warnings.filterwarnings("ignore", message="This pattern is interpreted as a regular expression")
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import normalize

SIGNALS = {   # share of rows in a segment that mention each concern (for reading, not for clustering)
    "price/cost":        r"price|cost|expensive|cheap|afford|\$\s?\d",
    "cancel/leave":      r"cancel|unsubscrib|leaving|switch(ed|ing)? (to|from)",
    "alternatives":      r"apple music|youtube music|tidal|amazon music|deezer|qobuz",
    "lossless/hifi":     r"lossless|hi-?fi|audio quality|bitrate|dolby|atmos",
    "ads/free tier":     r"\bads?\b|free tier|free version|free account",
    "artists/royalties": r"artist|royalt|payout|musicians?",
    "discovery/algo":    r"discover|algorithm|recommend|wrapped|\bdj\b|daylist|playlist",
    "podcasts/books":    r"podcast|audiobook",
    "bugs/app":          r"\bbug|crash|glitch|app (is|keeps)|update broke|login",
    "family/student":    r"family plan|duo|student|\bkids?\b",
}
FOCUS = re.compile(r"price|cost|expens|cheap|afford|premium|subscri|cancel|plan|family|student|worth|ads?\\b|free|"
                   r"apple music|youtube music|tidal|deezer|amazon music|lossless|hi-?fi|quality|artist|royalt|podcast|"
                   r"discover|algorithm|recommend|feature|update|\\bui\\b", re.I)
BOTLIKE = re.compile(r"i am a bot|this action was performed automatically|megathread|your post has been removed|please read the rules", re.I)


def clean(df, min_words):
    df = df[df.role == "persona_source"].copy() if "role" in df.columns else df.copy()
    df["text"] = df["text"].fillna("").astype(str)
    df["text"] = df["text"].str.replace(r"https?://\S+", " ", regex=True).str.replace(r"\s+", " ", regex=True).str.strip()
    df["word_count"] = df["text"].str.split().str.len()
    df = df[(df.word_count >= min_words) & ~df.text.str.contains(BOTLIKE)]
    df = df.drop_duplicates(subset="text")
    return df


def stratified_sample(df, n, seed):
    if len(df) <= n:
        return df.copy()
    df = df.copy()
    df["_m"] = pd.to_datetime(df["created_utc"], utc=True).dt.strftime("%Y-%m")
    frac = n / len(df)                                     # same fraction from every month so no period dominates
    out = df.groupby("_m", group_keys=False).apply(lambda g: g.sample(frac=frac, random_state=seed) if len(g) > 1 else g)
    return out.drop(columns="_m")


def embed(texts, backend, seed):
    if backend == "st":
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2")
            vecs = model.encode([t[:1200] for t in texts], batch_size=128, show_progress_bar=True, normalize_embeddings=True)
            return np.asarray(vecs), "sentence-transformers all-MiniLM-L6-v2"
        except ImportError:
            print("sentence-transformers not installed -> falling back to TF-IDF (lower quality). pip install sentence-transformers")
    tf = TfidfVectorizer(max_features=20000, ngram_range=(1, 2), min_df=3, max_df=0.5, stop_words="english", sublinear_tf=True)
    X = tf.fit_transform(texts)
    k = min(100, X.shape[1] - 1)
    Z = TruncatedSVD(n_components=k, random_state=seed).fit_transform(X)
    return normalize(Z), "TF-IDF + SVD (fallback)"


def pick_k(Z, k_min, k_max, seed):
    best, scores = None, {}
    idx = np.random.RandomState(seed).choice(len(Z), size=min(5000, len(Z)), replace=False)
    for k in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, n_init=10, random_state=seed).fit(Z)
        s = silhouette_score(Z[idx], km.labels_[idx])
        scores[k] = round(float(s), 4)
        if best is None or s > best[1]:
            best = (k, s)
    return best[0], scores


def top_terms(texts_by_seg, n=12):
    docs = [" ".join(t) for t in texts_by_seg]
    tf = TfidfVectorizer(max_features=30000, ngram_range=(1, 2), min_df=2, max_df=0.6, stop_words="english", sublinear_tf=True)
    X = tf.fit_transform(docs)                            # one document per segment -> distinctive words
    vocab = np.array(tf.get_feature_names_out())
    return [list(vocab[np.argsort(-X[i].toarray()[0])[:n]]) for i in range(X.shape[0])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="spotify_persona_core.csv")
    ap.add_argument("--outdir", default="task3_output")
    ap.add_argument("--min-words", type=int, default=15)
    ap.add_argument("--sample", type=int, default=30000)
    ap.add_argument("--focus", action="store_true", help="keep only rows that talk about pricing, plans, alternatives, quality, artists or features (drops pure how-to/support chatter)")
    ap.add_argument("--k", type=int, default=0, help="force a number of segments (default: best of 6-8)")
    ap.add_argument("--backend", choices=["st", "tfidf"], default="st")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()

    out = Path(a.outdir); out.mkdir(exist_ok=True)
    raw = pd.read_csv(a.input)
    df = clean(raw, a.min_words)
    if a.focus:
        df = df[df.text.str.contains(FOCUS)]
    print(f"{len(raw):,} rows in -> {len(df):,} after cleaning (>= {a.min_words} words, no bots/dupes)")
    df = stratified_sample(df, a.sample, a.seed).reset_index(drop=True)
    print(f"{len(df):,} rows sampled (even across months)")

    Z, how = embed(df["text"].tolist(), a.backend, a.seed)
    print("embedding:", how)
    if a.k:
        k, scores = a.k, {}
    else:
        k, scores = pick_k(Z, 6, 8, a.seed)
    print("silhouette by k:", scores, "-> using k =", k)

    km = KMeans(n_clusters=k, n_init=10, random_state=a.seed).fit(Z)
    df["segment_id"] = km.labels_
    df["dist_to_centroid"] = np.linalg.norm(Z - km.cluster_centers_[km.labels_], axis=1)

    terms = top_terms([df.loc[df.segment_id == s, "text"].tolist() for s in range(k)])
    profiles = []
    for s in range(k):
        g = df[df.segment_id == s]
        close = g[g.word_count >= 25].nsmallest(12, "dist_to_centroid") if (g.word_count >= 25).sum() >= 12 else g.nsmallest(12, "dist_to_centroid")
        low = g.text.str.lower()
        profiles.append({
            "segment_id": s, "size": int(len(g)), "share_pct": round(100 * len(g) / len(df), 1),
            "name": "", "top_terms": terms[s],
            "signal_rate_pct": {k_: round(100 * low.str.contains(p, regex=True).mean(), 1) for k_, p in SIGNALS.items()},
            "kind_mix": g.kind.value_counts(normalize=True).round(2).to_dict(),
            "subreddit_mix": g.subreddit.value_counts(normalize=True).round(2).head(3).to_dict(),
            "unique_authors": int(g.author_hash.nunique()) if "author_hash" in g else None,
            "median_words": int(g.word_count.median()),
            "examples": [{"uid": r.uid, "created": str(r.created_utc)[:10], "text": r.text[:500]} for r in close.itertuples()],
        })

    df.to_csv(out / "persona_sample_segmented.csv", index=False)
    (out / "segment_profiles.json").write_text(json.dumps({"embedding": how, "k": k, "silhouette": scores, "segments": profiles}, indent=2))

    md = [f"# Spotify community segments (k = {k}, {len(df):,} rows, {how})\n",
          "Read each segment, then replace `Name: ___` with a short human label (e.g. 'Audio-quality fans').\n"]
    for p in profiles:
        top_sig = sorted(p["signal_rate_pct"].items(), key=lambda kv: -kv[1])[:4]
        md += [f"\n## Segment {p['segment_id']}  -  {p['size']:,} rows ({p['share_pct']}%)\n", "**Name:** ___\n",
               f"**Distinctive terms:** {', '.join(p['top_terms'])}\n",
               "**Most-mentioned concerns:** " + ", ".join(f"{k_} {v}%" for k_, v in top_sig) + "\n",
               f"**Mix:** {p['kind_mix']} | subreddits {p['subreddit_mix']} | {p['unique_authors']} distinct authors\n", "**Example rows (closest to the segment's center):**\n"]
        md += [f"- ({e['created']}) {e['text'][:300]}" for e in p["examples"][:8]]
    (out / "segment_profiles.md").write_text("\n".join(md))
    print("\nWrote:", *(str(out / f) for f in ("persona_sample_segmented.csv", "segment_profiles.json", "segment_profiles.md")), sep="\n  ")
    print("\nNEXT: open segment_profiles.md, name each segment, check sizes. Warning signs: a segment under 3% or over 40%, or two segments with near-identical terms.")


if __name__ == "__main__":
    main()
