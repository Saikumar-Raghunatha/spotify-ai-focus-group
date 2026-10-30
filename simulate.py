#!/usr/bin/env python3
"""
TASK 5: simulate the community's reaction to a price announcement, plus two baselines.

    python simulate.py prep    [--event 2023]   # write one brief per (condition, repetition) to sim_<event>/briefs/
    (one persona-sim agent per brief, Haiku, Read/Write only, writes sim_<event>/out/<condition>_r<k>.json)
    python simulate.py collect [--event 2023]   # validate + merge into sim_<event>/results.csv and summary.md

Conditions (5 repetitions each, persona order reshuffled every repetition):
    rag    persona profile + 8 of the persona's own pre-cutoff posts retrieved for the announcement
    norag  persona profile only
    plain  no personas: "simulate 26 r/spotify users" (the plain ChatGPT-style baseline)

The label sets below are fixed BEFORE looking at the post-event data; Task 6 labels the real posts with the same sets.
"""
import argparse, json, random, re
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
REPS = 5
K_POSTS = 8

ANNOUNCEMENTS = {
    "2023": {
        "date": "2023-07-24",
        "personas": "personas",
        "text": (
            "Spotify announcement, July 24, 2023: Spotify is raising the price of Premium in the US and dozens of other "
            "markets. US prices: Premium Individual goes from $9.99 to $10.99 per month, Duo from $12.99 to $14.99, "
            "Family from $15.99 to $16.99, and Student from $4.99 to $5.99. This is the first US price increase for "
            "Premium since Spotify launched in the US in 2011. Spotify says the change will let it keep investing in "
            "the product and deliver value to fans and artists. New prices apply to new subscribers now; existing "
            "subscribers will be notified by email before their price changes."),
    },
    "2026": {
        "date": "2026-01-15",
        "personas": "personas_2026",
        "text": (
            "Spotify announcement, January 15, 2026: Spotify is raising the price of Premium in the US (and in Estonia "
            "and Latvia). US prices: Premium Individual goes from $11.99 to $12.99 per month, Duo from $16.99 to "
            "$18.99, Family from $19.99 to $21.99, and Student from $5.99 to $6.99. Spotify says the change will let it "
            "continue offering the best possible experience and benefit artists. Existing subscribers will get an "
            "email, and the new price applies from their February 2026 billing date."),
    },
}

ACTIONS = ["cancel", "switch", "downgrade", "complain", "accept", "ignore"]
ACTION_HELP = ("cancel = will cancel Premium / go free with no named alternative; switch = will move to a named competitor; "
               "downgrade = moves to a cheaper plan or tier; complain = unhappy but staying; accept = fine with it or defends "
               "Spotify; ignore = does not care / indifferent")
SENTIMENTS = ["very_negative", "negative", "neutral", "positive"]
THEMES = {
    "greed_corporate": "Spotify/executives are greedy, profit over users",
    "artist_pay": "artists/royalties, will artists get more money",
    "still_good_value": "still worth it / cheap for what you get",
    "inflation_expected": "inflation, overdue, other services already raised prices",
    "competitor_comparison": "compares to Apple Music, YouTube Music, Tidal, Amazon etc.",
    "plan_cost": "Family, Duo or Student plan cost specifically",
    "lossless_missing": "paying more but still no HiFi/lossless",
    "podcast_audiobook_spending": "money wasted on podcasts/audiobooks/Rogan instead of music",
    "app_quality_ui": "app getting worse, UI redesign, bugs, features removed",
    "ads_free_tier": "ads, free tier, going back to free",
    "affordability": "personal budget, can't afford, cost of living",
    "piracy": "piracy or downloading instead",
}

OUTPUT_SPEC = f"""Output: write ONE JSON array to the output file, one object per {{who}}, with exactly these keys:
  "id": {{id_hint}}
  "comment": what they would post in an r/spotify thread about this announcement (1-4 sentences, their own voice)
  "sentiment": one of {SENTIMENTS}
  "action": one of {ACTIONS}  ({ACTION_HELP})
  "switch_to": name of the service if action is "switch", else null
  "themes": 1-3 items from this list only: {list(THEMES)}
  "intensity": integer 1 (barely cares) to 5 (furious or thrilled)
Theme meanings: {json.dumps(THEMES)}
React only as strongly as this person plausibly would; real communities include people who shrug, defend the company,
or just complain and stay. "ignore" and "accept" are valid answers."""


def retrieve(event_cfg):
    import sys
    sys.path.insert(0, str(HERE))
    from persona_retriever import Retriever
    r = Retriever(HERE / event_cfg["personas"])
    q = r.embed(event_cfg["text"])
    return {pid: r.search(pid, "", k=K_POSTS, query_vec=q) for pid in r._by_persona}


def persona_block(p, posts):
    s = f"=== PERSONA {p['persona_id']} ===\n{p['system_prompt']}\n"
    if posts:
        s += "Some of your own past posts (for your voice and opinions; all written before the announcement):\n"
        s += "\n".join(f"- ({h['created_utc'][:10]}) {re.sub(r'\s+', ' ', h['text'])[:300]}" for h in posts) + "\n"
    return s


def prep(event, tag="", conds=("rag", "norag", "plain")):
    cfg = dict(ANNOUNCEMENTS[event])
    if tag:
        cfg["personas"] = f"{cfg['personas']}_{tag}"
    root = HERE / (f"sim_{event}_{tag}" if tag else f"sim_{event}")
    (root / "briefs").mkdir(parents=True, exist_ok=True); (root / "out").mkdir(exist_ok=True)
    personas = json.loads((HERE / cfg["personas"] / "personas.json").read_text())["personas"]
    hits = retrieve(cfg)
    (root / "retrieved.json").write_text(json.dumps(hits, indent=1))
    n = len(personas)
    for cond in conds:
        for k in range(1, REPS + 1):
            out = root / "out" / f"{cond}_r{k}.json"
            if cond == "plain":
                body = (f"Task: simulate how {n} different members of the r/spotify subreddit would each react to the "
                        f"announcement below. Make them a realistic mix of the community.\n\nANNOUNCEMENT:\n{cfg['text']}\n\n"
                        + OUTPUT_SPEC.replace("{who}", "simulated member").replace("{id_hint}", f'"u1" to "u{n}"'))
            else:
                order = personas[:]
                random.Random(f"{cond}{k}").shuffle(order)
                blocks = "\n".join(persona_block(p, hits[p["persona_id"]] if cond == "rag" else None) for p in order)
                body = (f"Task: below are {n} independent personas. For EACH persona separately, imagine they have just read "
                        f"the announcement and write their reaction in character. Each persona knows only its own block; "
                        f"do not let personas copy or influence each other.\n\nANNOUNCEMENT:\n{cfg['text']}\n\n"
                        + OUTPUT_SPEC.replace("{who}", "persona").replace("{id_hint}", "the persona id, e.g. \"s1_p1\"")
                        + f"\n\nPERSONAS:\n{blocks}")
            (root / "briefs" / f"{cond}_r{k}.md").write_text(f"OUTPUT FILE: {out}\n\n{body}\n")
    print(f"wrote {len(conds) * REPS} briefs ({n} personas) to {root / 'briefs'}")


def collect(event, tag=""):
    root = HERE / (f"sim_{event}_{tag}" if tag else f"sim_{event}")
    rows, problems = [], []
    for f in sorted((root / "out").glob("*.json")):
        cond, rep = f.stem.rsplit("_r", 1)
        try:
            items = json.loads(f.read_text())
        except Exception as e:
            problems.append(f"{f.name}: invalid JSON ({e})"); continue
        for it in items:
            it = {**it, "condition": cond, "rep": int(rep)}
            bad = [k for k, ok in [("action", it.get("action") in ACTIONS), ("sentiment", it.get("sentiment") in SENTIMENTS)] if not ok]
            it["themes"] = [t for t in (it.get("themes") or []) if t in THEMES]
            if bad:
                problems.append(f"{f.name} {it.get('id')}: bad {bad}")
            rows.append(it)
    d = pd.DataFrame(rows)
    d["themes"] = d.themes.apply(lambda t: "|".join(t))
    d.to_csv(root / "results.csv", index=False)

    L = [f"# Simulation summary ({event})\n", f"{len(d)} responses. Shares are mean ± sd across repetitions.\n"]
    for col, cats in (("action", ACTIONS), ("sentiment", SENTIMENTS), ("themes", list(THEMES))):
        t = []
        for cond, g in d.groupby("condition"):
            per_rep = g.groupby("rep").apply(lambda x: pd.Series({c: (x[col].str.split("|").apply(lambda v: c in v)).mean() for c in cats}))
            t.append((per_rep.mean().map("{:.0%}".format) + " ± " + per_rep.std().fillna(0).map("{:.0%}".format)).rename(cond))
        L.append(f"\n## {col}\n\n" + pd.concat(t, axis=1).to_markdown() + "\n")
    if problems:
        L.append("\n## Validation problems\n\n" + "\n".join(f"- {p}" for p in problems))
    (root / "summary.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["prep", "collect"])
    ap.add_argument("--event", default="2023")
    ap.add_argument("--tag", default="", help="persona-set version, e.g. v2 -> personas_v2/ and sim_<event>_v2/")
    ap.add_argument("--conds", default="rag,norag,plain")
    a = ap.parse_args()
    prep(a.event, a.tag, tuple(a.conds.split(","))) if a.step == "prep" else collect(a.event, a.tag)
