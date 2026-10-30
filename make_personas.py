#!/usr/bin/env python3
"""
TASK 4: build 26 persona agents (7+7+5+5+2) from the Task 3 segments, each with its own retrieval pool.

    python make_personas.py              # step 1: build pools + index, write one evidence brief per persona
    (Claude Code Haiku subagents read personas/drafts/<id>_brief.md and write personas/drafts/<id>.json; no API)
    python make_personas.py --finalize   # step 2: merge the drafted profiles, add system prompts, flag hindsight

Input : persona_sample_segmented.csv (Task 3), persona_config.json
Output: personas/
    personas.json      one record per persona: profile, system prompt, pool stats, evidence uids
    persona_cards.md   human-readable cards to review
    index/rows.parquet, index/embeddings.npy   the retrieval store (persona_retriever.py reads it)

How personas are formed inside a segment:
    1. "anchor" personas (from persona_config.json): rows matching the anchor regex, first match wins
       (e.g. students, family-plan users, Apple Music switchers). Gives the archetypes the brief asks for.
    2. the remaining personas: KMeans on the leftover rows' embeddings, so they are data-driven sub-types.
Every row belongs to exactly one persona, so pools never overlap.

Leakage guards: only role == persona_source rows dated before the cutoff are used; the profile prompt forbids
anything after the cutoff; profiles are scanned for hindsight terms and flagged.
"""
import argparse, json, re, sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

HERE = Path(__file__).resolve().parent
EMB_MODEL = "all-MiniLM-L6-v2"
HINDSIGHT = re.compile(r"10\.99|11\.99|12\.99|price (hike|increase)|raised (its |their )?prices?|"
                       r"price went up|july 2023|stock (fell|dropped|rose)", re.I)

SYSTEM = ("You write research personas for a marketing-analytics class project. You get real Reddit posts and comments "
          "written by members of one online community before a cutoff date. Describe only what the evidence supports. "
          "Return a single JSON object and nothing else.")

PROMPT = """Community segment: {segment}
Persona focus: {focus}
Keyword signals in this persona's posts (share of rows): {signals}

Below are {n} real posts/comments that make up ONE persona (all dated before {cutoff}).
Write the persona as one JSON object with exactly these keys:
"name": a plausible first name
"label": 3-6 word descriptive label
"who": 2 sentences, first person, who I am as a Spotify user (plan type, how I listen, what I care about)
"value_for_money": what they say or imply about price, value, free vs paid ("unclear" if the evidence does not say)
"price_sensitivity": "low" | "medium" | "high" | "unclear"
"loyalty": what keeps them on Spotify and what would make them leave
"pain_points": up to 4 short strings
"likes": up to 3 short strings
"alternatives_mentioned": services they name (may be empty)
"tone": one sentence on how they write
"typical_phrases": up to 6 short phrases (max 4 words) in their voice
"evidence_ids": the [numbers] of the 5 posts that best support this profile

Rules: use ONLY the evidence; do not invent facts; mention nothing after {cutoff}; do NOT predict how they would react to
any price change; no usernames.

EVIDENCE:
{evidence}"""

# v2 (tuning round on 2023): reasons to stay get the same weight as pain points
PROMPT_V2 = PROMPT.replace(
    '"likes": up to 3 short strings',
    '"likes": up to 4 short strings\n"reasons_to_stay": 2-3 sentences on what they value and why they keep using Spotify, as '
    'concrete as the pain points ("unclear" only if the evidence says nothing)').replace(
    "any price change; no usernames.",
    "any price change; no usernames. Give what they like and why they stay the same weight as their complaints: people "
    "who complain about one feature often still value the service overall.")

PERSONA_SYSTEM = """You are {name}, a real member of the r/spotify community. {who}

About you:
- Value for money: {value_for_money}
- Price sensitivity: {price_sensitivity}
- Loyalty: {loyalty}
- Pain points: {pain_points}
- What you like: {likes}
- Alternatives you have mentioned: {alts}
- How you write: {tone} Phrases you use: {phrases}

Stay in character. Write like a Reddit commenter, not an assistant. You only know what had happened up to {cutoff}."""


PERSONA_SYSTEM_V2 = PERSONA_SYSTEM.replace(
    "- Pain points: {pain_points}\n- What you like: {likes}",
    "- What you like: {likes}\n- Why you stay: {reasons_to_stay}\n- Pain points: {pain_points}")
V2 = False   # set from the config's "version"


def load_rows(path, cutoff):
    d = pd.read_csv(path)
    d = d[(d.role == "persona_source") & (d.created_utc < cutoff)]
    d = d.dropna(subset=["text"]).drop_duplicates("text")
    return d.reset_index(drop=True)


def embed(texts):
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(EMB_MODEL)
    return np.asarray(m.encode(texts, batch_size=128, show_progress_bar=True, normalize_embeddings=True), dtype="float32")


def assign_personas(seg_rows, seg_emb, sc, seed):
    """Return (persona index per row, focus label per persona)."""
    n = sc["personas"]
    anchors = sc.get("anchors", {})
    out = np.full(len(seg_rows), -1)
    focus = []
    low = seg_rows.text.str.lower().values
    for j, (label, rx) in enumerate(anchors.items()):
        pat = re.compile(rx, re.I)
        hit = np.array([bool(pat.search(t)) for t in low]) & (out == -1)
        out[hit] = j
        focus.append(f"anchor: {label}")
    rest = np.where(out == -1)[0]
    k = n - len(anchors)
    km = KMeans(k, n_init=10, random_state=seed).fit(seg_emb[rest])
    out[rest] = len(anchors) + km.labels_
    for c in range(k):
        focus.append("sub-cluster: " + top_terms(seg_rows.text.values[rest][km.labels_ == c],
                                                 seg_rows.text.values[rest][km.labels_ != c]))
    return out, focus


def top_terms(inside, outside, k=8):
    from sklearn.feature_extraction.text import TfidfVectorizer
    tf = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=3, max_features=20000)
    X = tf.fit_transform(list(inside) + list(outside))
    a = np.asarray(X[:len(inside)].mean(0)).ravel() - np.asarray(X[len(inside):].mean(0)).ravel()
    terms = tf.get_feature_names_out()
    return ", ".join(terms[i] for i in a.argsort()[::-1][:k])


SIGNALS = {"student": r"\bstudent", "family/duo plan": r"family plan|family account|\bduo\b",
           "price talk": r"\bprice|\$\d|expensive|afford|cheap", "cancel talk": r"cancel|unsubscrib",
           "apple music": r"apple music", "youtube music": r"youtube music|yt music", "tidal": r"\btidal\b",
           "artist pay": r"royalt|pay(?:ing)? artists|artists? (?:get|are) paid", "lossless/hifi": r"lossless|hifi|hi-fi"}


def signals(texts):
    low = pd.Series(texts).str.lower()
    s = {k: low.str.contains(v, regex=True).mean() for k, v in SIGNALS.items()}
    return ", ".join(f"{k} {v:.0%}" for k, v in sorted(s.items(), key=lambda x: -x[1]) if v >= 0.02) or "none above 2%"


def pick_evidence(pool, emb, n=40, n_price=10, value_rx=None, n_value=8):
    """Most typical rows (closest to the persona centroid), up to n_price price-related rows and (v2) up to n_value
    rows that praise or value the service."""
    c = emb.mean(0); c /= np.linalg.norm(c)
    order = np.argsort(-(emb @ c))
    price = [i for i in order if pool.price_related.iloc[i]][:n_price]
    value = []
    if value_rx:
        hit = pool.text.str.contains(value_rx, case=False, regex=True).values
        value = [i for i in order if hit[i] and i not in set(price)][:n_value]
    taken = set(price) | set(value)
    typical = [i for i in order if i not in taken][: n - len(taken)]
    return sorted(price + value + typical, key=lambda i: pool.created_utc.iloc[i])


def brief(segment, focus, sig, ev_rows, cutoff):
    ev = "\n".join(f"[{i}] ({r.created_utc[:10]}) {re.sub(r'\s+', ' ', r.text)[:400]}"
                   for i, r in enumerate(ev_rows.itertuples()))
    return SYSTEM + "\n\n" + (PROMPT_V2 if V2 else PROMPT).format(segment=segment, focus=focus, signals=sig, n=len(ev_rows),
                                             cutoff=cutoff, evidence=ev)


def persona_system(p, cutoff):
    j = lambda x: "; ".join(x) if isinstance(x, list) and x else "none"
    return (PERSONA_SYSTEM_V2 if V2 else PERSONA_SYSTEM).format(name=p.get("name", "a user"), who=p.get("who", ""),
                                 reasons_to_stay=p.get("reasons_to_stay", "unclear"),
                                 value_for_money=p.get("value_for_money", "unclear"),
                                 price_sensitivity=p.get("price_sensitivity", "unclear"),
                                 loyalty=p.get("loyalty", ""), pain_points=j(p.get("pain_points")),
                                 likes=j(p.get("likes")), alts=j(p.get("alternatives_mentioned")),
                                 tone=p.get("tone", ""), phrases=j(p.get("typical_phrases")), cutoff=cutoff)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(HERE / "persona_sample_segmented.csv"))
    ap.add_argument("--config", default=str(HERE / "persona_config.json"))
    ap.add_argument("--outdir", default=str(HERE / "personas"))
    ap.add_argument("--finalize", action="store_true", help="merge drafts/<id>.json into personas.json")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()

    out = Path(a.outdir)
    if a.finalize:
        return finalize(out)
    global V2
    cfg = json.loads(Path(a.config).read_text())
    cutoff = cfg["cutoff"]
    V2 = cfg.get("version") == "v2"
    sat = cfg.get("satisfied")
    (out / "index").mkdir(parents=True, exist_ok=True); (out / "drafts").mkdir(exist_ok=True)

    rows = load_rows(a.input, cutoff)
    rows = rows[rows.segment_id.astype(str).isin(cfg["segments"].keys())].reset_index(drop=True)
    for sid, sc in cfg["segments"].items():
        if sc.get("exclude_regex"):
            bad = (rows.segment_id.astype(str) == sid) & rows.text.str.contains(sc["exclude_regex"], case=False, regex=True)
            rows = rows[~bad]
    rows = rows.reset_index(drop=True)
    print(f"{len(rows):,} persona-source rows before {cutoff} in segments {list(cfg['segments'])}")

    emb = embed(rows.text.str.slice(0, 1200).tolist())

    rows["persona_id"] = ""
    personas = []
    for sid, sc in cfg["segments"].items():
        idx = np.where(rows.segment_id.astype(str) == sid)[0]
        assign, focus = assign_personas(rows.iloc[idx], emb[idx], sc, a.seed)
        n_p = sc["personas"]
        if sat:
            seg = rows.iloc[idx]
            hit = (seg.text.str.contains(sat["regex"], case=False, regex=True)
                   & seg.text.str.contains(sat["context"], case=False, regex=True)).values
            if hit.sum() >= sat["min_rows"]:
                assign[hit] = n_p; n_p += 1; focus.append("anchor: satisfied subscribers")
            print(f"segment {sid}: {int(hit.sum())} satisfied rows" + ("" if hit.sum() >= sat["min_rows"] else " (below minimum, no persona)"))
        for j in range(n_p):
            pid = f"s{sid}_p{j + 1}"
            pidx = idx[assign == j]
            rows.loc[pidx, "persona_id"] = pid
            pool = rows.iloc[pidx]
            ev_local = pick_evidence(pool, emb[pidx], value_rx=sat["regex"] if sat else None)
            ev_rows = pool.iloc[ev_local]
            sig = signals(pool.text.values)
            rec = {"persona_id": pid, "segment_id": sid, "segment": sc["name"], "focus": focus[j],
                   "pool_rows": int(len(pool)), "pool_authors": int(pool.author_hash.nunique()),
                   "signals": sig, "evidence_uids": ev_rows.uid.tolist()}
            (out / "drafts" / f"{pid}_brief.md").write_text(brief(sc["name"], focus[j], sig, ev_rows, cutoff))
            print(f"{pid:8s} {len(pool):5d} rows  {focus[j]}")
            personas.append(rec)

    keep = rows.persona_id != ""
    rows[keep][["uid", "persona_id", "segment_id", "created_utc", "kind", "score", "text", "price_related"]] \
        .reset_index(drop=True).to_parquet(out / "index" / "rows.parquet")
    np.save(out / "index" / "embeddings.npy", emb[keep.values])
    (out / "index" / "meta.json").write_text(json.dumps({"embedding_model": EMB_MODEL, "cutoff": cutoff, "rows": int(keep.sum())}))
    (out / "personas.json").write_text(json.dumps({"cutoff": cutoff, "version": cfg.get("version", "v1"), "personas": personas}, indent=2))
    write_cards(out / "persona_cards.md", personas, rows)
    print(f"Wrote {out}/personas.json, persona_cards.md, index/ ({int(keep.sum()):,} rows), drafts/*_brief.md")


def finalize(out):
    global V2
    data = json.loads((out / "personas.json").read_text())
    cutoff = data["cutoff"]
    V2 = data.get("version") == "v2"
    rows = pd.read_parquet(out / "index" / "rows.parquet")
    missing, used = [], set()
    spare = iter(["Elena", "Marco", "Tasha", "Owen", "Lina", "Felix", "Grace", "Hugo", "Iris", "Jonah", "Keira", "Luis",
                  "Mona", "Nadia", "Oscar", "Pia", "Quinn", "Rosa", "Sven", "Tara", "Uma", "Vik", "Wren", "Yara", "Zane"])
    for rec in data["personas"]:
        f = out / "drafts" / f"{rec['persona_id']}.json"
        if not f.exists():
            missing.append(rec["persona_id"]); continue
        prof = json.loads(f.read_text())
        if prof.get("name") in used:     # agents drafted segments independently, so first names can repeat
            prof["name"] = next(n for n in spare if n not in used)
        used.add(prof.get("name"))
        ev = rec["evidence_uids"]
        prof["evidence_uids"] = [ev[i] for i in prof.pop("evidence_ids", []) if isinstance(i, int) and 0 <= i < len(ev)]
        flags = HINDSIGHT.findall(json.dumps(prof))
        rec.update(profile=prof, system_prompt=persona_system(prof, cutoff), hindsight_flags=flags)
        print(f"{rec['persona_id']:8s} {prof.get('name')}: {prof.get('label')}" + (f"  FLAG {flags}" if flags else ""))
    data["drafted_by"] = "Claude Code subagents (claude-haiku), no API calls"
    (out / "personas.json").write_text(json.dumps(data, indent=2))
    write_cards(out / "persona_cards.md", data["personas"], rows)
    print(f"merged {len(data['personas']) - len(missing)} profiles" + (f"; MISSING {missing}" if missing else ""))


def write_cards(path, personas, rows):
    by_uid = rows.set_index("uid").text
    L = ["# Persona cards (Task 4)\n", f"{len(personas)} personas. Review each card; edit persona_config.json and re-run if a persona looks wrong.\n"]
    seg = None
    for p in personas:
        if p["segment"] != seg:
            seg = p["segment"]; L.append(f"\n## {seg}\n")
        pr = p.get("profile", {})
        L.append(f"### {p['persona_id']}: {pr.get('name', '')} - {pr.get('label', p['focus'])}\n")
        L.append(f"*{p['focus']}* | pool {p['pool_rows']:,} rows from {p['pool_authors']:,} authors | signals: {p['signals']}\n")
        if pr:
            L.append(f"> {pr.get('who', '')}\n")
            L.append(f"- **Price sensitivity:** {pr.get('price_sensitivity')} | **Value:** {pr.get('value_for_money')}")
            L.append(f"- **Loyalty:** {pr.get('loyalty')}")
            L.append(f"- **Pain points:** {', '.join(pr.get('pain_points', []))}")
            L.append(f"- **Alternatives:** {', '.join(pr.get('alternatives_mentioned', [])) or 'none'}")
            L.append(f"- **Tone:** {pr.get('tone')}")
            if p.get("hindsight_flags"):
                L.append(f"- **HINDSIGHT FLAG:** {p['hindsight_flags']}")
        L.append("\nSupporting posts:")
        for u in (pr.get("evidence_uids") or p["evidence_uids"])[:3]:
            L.append(f"- {re.sub(r'\s+', ' ', str(by_uid.get(u, '')))[:220]}")
        L.append("")
    Path(path).write_text("\n".join(L))


if __name__ == "__main__":
    main()
