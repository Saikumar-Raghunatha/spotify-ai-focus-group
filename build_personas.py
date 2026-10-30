#!/usr/bin/env python3
"""
TASK 4: turn the named segments into persona agents with their own retrieval evidence.

Input : persona_sample_segmented.csv   (from Task 3, the --focus run)
Config: config.json                    (which segments to keep, names, how many personas each)

Run   : python build_personas.py --input ../task3_output_final/persona_sample_segmented.csv
        (needs ANTHROPIC_API_KEY set for the profile drafting; add --no-llm to skip it)

How personas stay different from each other: each segment's AUTHORS are split into groups, one group per persona,
so every persona has its own non-overlapping pool of real pre-event posts to retrieve from and to be described by.

Outputs (./task4_output):
    personas.json      profile + evidence ids for every persona   (Task 5 reads this)
    persona_cards.md   human-readable cards for the team to review
    index/             embeddings + rows for retrieval            (Task 5 uses persona_index.py)
"""
import argparse, json, os, re, sys, time
from pathlib import Path
import numpy as np
import pandas as pd
from persona_index import embed_corpus

SYSTEM = ("You write research personas for a marketing-analytics class project. You are given real Reddit posts and comments "
          "written by members of one online community BEFORE a specific cutoff date. Describe only what the evidence supports.")

PROMPT = """Community segment: {segment}

Below are {n} real posts/comments from the members who make up ONE persona (dates are all before {cutoff}).
Write a persona profile as a single JSON object with exactly these keys:
- "label": 3-6 word descriptive label
- "summary": 3-4 sentences, third person, what this person is like as a Spotify user
- "value_for_money": what they say or imply about price, value, free vs paid ("unclear" if the evidence does not say)
- "price_sensitivity": one of "low", "medium", "high", "unclear"
- "loyalty": why they stay or what would make them leave
- "pain_points": list of up to 4 short strings
- "likes": list of up to 3 short strings
- "alternatives_mentioned": list of services they name (may be empty)
- "tone": one sentence on how they write (formality, humor, anger, politeness)
- "typical_phrases": up to 6 short phrases (max 4 words each) that capture their voice
- "evidence_ids": list of the numbers of the posts that most support this profile

Rules: use ONLY the evidence; do not invent facts; do not mention any event after {cutoff}; do NOT predict how they would react to any price change; no usernames. Return JSON only.

EVIDENCE:
{evidence}
"""


def split_pools(rows, n, seed):
    """Partition authors into n groups (greedy, by row count) so personas get balanced, non-overlapping pools."""
    rng = np.random.RandomState(seed)
    counts = rows[rows.author_hash.notna() & (rows.author_hash != "")].groupby("author_hash").size()
    authors = list(counts.index)
    rng.shuffle(authors)
    authors.sort(key=lambda a: -counts[a])
    load, assign = [0] * n, {}
    for a in authors:
        j = int(np.argmin(load)); assign[a] = j; load[j] += counts[a]
    out = []
    for r in rows.itertuples():
        a = getattr(r, "author_hash", "")
        out.append(assign[a] if isinstance(a, str) and a in assign else int(rng.randint(n)))
    return np.array(out)


def parse_json(text):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    return json.loads(text[text.index("{"): text.rindex("}") + 1])


def draft_profile(client, model, segment, ev, cutoff):
    evidence = "\n".join(f"[{i}] ({str(r.created_utc)[:10]}) {r.text[:700]}" for i, r in enumerate(ev.itertuples(), 1))
    msg = PROMPT.format(segment=segment, n=len(ev), cutoff=cutoff, evidence=evidence)
    last = None
    for attempt in range(3):
        try:
            resp = client.messages.create(model=model, max_tokens=1500, system=SYSTEM, messages=[{"role": "user", "content": msg}])
            prof = parse_json(resp.content[0].text)
            prof["evidence_ids"] = [ev.iloc[i - 1].uid for i in prof.get("evidence_ids", []) if isinstance(i, int) and 1 <= i <= len(ev)]
            return prof
        except Exception as e:
            last = e; time.sleep(2)
    raise RuntimeError(f"profile drafting failed: {last}")


def rule_profile(ev):
    low = ev.text.str.lower()
    pr = float(low.str.contains(r"price|cost|expens|cheap|afford|worth it|\$\d").mean())
    return {"label": "(not drafted: run without --no-llm)", "summary": "", "value_for_money": "unclear",
            "price_sensitivity": "high" if pr > 0.3 else ("medium" if pr > 0.1 else "unclear"),
            "loyalty": "", "pain_points": [], "likes": [], "alternatives_mentioned": [], "tone": "",
            "typical_phrases": [], "evidence_ids": ev.nsmallest(5, "dist_to_centroid").uid.tolist() if "dist_to_centroid" in ev else ev.uid.head(5).tolist()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="persona_sample_segmented.csv")
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--outdir", default="task4_output")
    ap.add_argument("--backend", choices=["st", "tfidf"], default="st")
    ap.add_argument("--model", default="claude-haiku-5-5", help="Claude model for profile drafting (check current model names)")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--evidence-n", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()

    cfg = json.loads(Path(a.config).read_text())
    cutoff = cfg.get("pre_event_cutoff", "2023-07-21")
    n_ev = a.evidence_n or cfg.get("evidence_per_persona", 30)
    out = Path(a.outdir); (out / "index").mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(a.input)
    df["author_hash"] = df.get("author_hash", pd.Series([""] * len(df))).fillna("")
    late = pd.to_datetime(df.created_utc, utc=True) >= pd.Timestamp(cutoff, tz="UTC")
    if late.any():
        sys.exit(f"STOP: {int(late.sum())} rows are dated on/after {cutoff}. Personas must only use pre-event data.")

    client = None
    if not a.no_llm:
        try:
            import anthropic
            client = anthropic.Anthropic()
        except Exception as e:
            sys.exit(f"Could not start the Anthropic client ({e}). pip install anthropic, set ANTHROPIC_API_KEY, or use --no-llm.")

    personas, pool_rows = [], []
    for sid, sc in cfg["segments"].items():
        seg = df[df.segment_id == int(sid)].copy()
        if sc.get("exclude_regex"):
            seg = seg[~seg.text.str.contains(sc["exclude_regex"], case=False, regex=True)]
        n = int(sc["personas"])
        grp = split_pools(seg, n, a.seed + int(sid))
        print(f"Segment {sid} '{sc['name']}': {len(seg):,} rows -> {n} personas")
        for j in range(n):
            pool = seg[grp == j]
            pid = f"S{sid}-P{j + 1}"
            ev = pool[pool.word_count >= 20] if (pool.word_count >= 20).sum() >= n_ev else pool
            ev = ev.sample(n=min(n_ev, len(ev)), random_state=a.seed + j).reset_index(drop=True)
            prof = rule_profile(ev) if a.no_llm else draft_profile(client, a.model, sc["name"], ev, cutoff)
            personas.append({"persona_id": pid, "segment_id": int(sid), "segment_name": sc["name"],
                             "pool_size": int(len(pool)), "authors": int(pool.author_hash.replace("", np.nan).nunique()),
                             "profile": prof, "voice_sample_uids": ev.uid.tolist()})
            p = pool.copy(); p["persona_id"] = pid
            pool_rows.append(p[["persona_id", "uid", "created_utc", "text"]])
            print(f"   {pid}: pool {len(pool):,} rows | {prof.get('label')}")

    rows = pd.concat(pool_rows, ignore_index=True)
    emb, meta = embed_corpus(rows.text.tolist(), a.backend, outdir=out / "index", seed=a.seed)
    np.save(out / "index" / "embeddings.npy", emb)
    rows.to_csv(out / "index" / "rows.csv", index=False)
    (out / "index" / "meta.json").write_text(json.dumps(meta))
    (out / "personas.json").write_text(json.dumps(personas, indent=2))

    md = ["# Persona cards (review and edit before simulating)\n",
          "Each persona is built ONLY from pre-July-21-2023 posts by its own group of authors.\n"]
    for p in personas:
        pr = p["profile"]
        md += [f"\n## {p['persona_id']}: {pr.get('label')}  ({p['segment_name']})\n",
               f"Pool: {p['pool_size']:,} rows, {p['authors']} authors | price sensitivity: **{pr.get('price_sensitivity')}**\n",
               pr.get("summary", ""), f"\n- **Value for money:** {pr.get('value_for_money')}", f"- **Loyalty:** {pr.get('loyalty')}",
               f"- **Pain points:** {'; '.join(pr.get('pain_points', []))}", f"- **Likes:** {'; '.join(pr.get('likes', []))}",
               f"- **Alternatives:** {', '.join(pr.get('alternatives_mentioned', []))}", f"- **Tone:** {pr.get('tone')}",
               f"- **Typical phrases:** {', '.join(pr.get('typical_phrases', []))}", "\n**Supporting real posts:**"]
        byuid = rows.drop_duplicates("uid").set_index("uid").text
        md += [f"- {byuid.get(u, '')[:260]}" for u in pr.get("evidence_ids", [])[:4]]
    (out / "persona_cards.md").write_text("\n".join(md))
    print(f"\nDone: {len(personas)} personas, {len(rows):,} retrievable rows -> {out}/")
    print("NEXT: read persona_cards.md. Check for (1) personas that sound identical, (2) all-angry personas, (3) any claim not backed by a supporting post.")


if __name__ == "__main__":
    main()
