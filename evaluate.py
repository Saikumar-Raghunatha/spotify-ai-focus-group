#!/usr/bin/env python3
"""
TASK 6: label the real post-event reaction, then score the simulation against it.

    python evaluate.py prep-labels  [--event 2023]   # write labeling briefs (Haiku subagents label them, no API)
    python evaluate.py collect-labels                # merge labels -> eval_<event>/real_labels.csv + handcheck sheet
    python evaluate.py score                         # metrics, hindsight check, charts -> eval_<event>/

Real rows = the price-hike threads (posts whose text is price-related, plus every comment inside them) and any other
price-related row in the post-event window. Labels use exactly the same ACTIONS / SENTIMENTS / THEMES as simulate.py,
plus "none" for real rows with no stated intention (questions, info, jokes) and a relevance flag.
"""
import argparse, json, re
from pathlib import Path
import numpy as np
import pandas as pd
from simulate import ACTIONS, ACTION_HELP, SENTIMENTS, THEMES

HERE = Path(__file__).resolve().parent
GT = {"2023": HERE / "spotify_ground_truth_core.csv",
      "2026": HERE / "holdout_2026" / "ground_truth_core_2026.csv"}    # written by holdout_2026_prepare.py
COMMUNITY = {"spotify", "truespotify"}
BATCH = 150

PRICES = {"2023": "Individual $9.99 -> $10.99, Duo $12.99 -> $14.99, Family $15.99 -> $16.99, Student $4.99 -> $5.99",
          "2026": "Individual $11.99 -> $12.99, Duo $16.99 -> $18.99, Family $19.99 -> $21.99, Student $5.99 -> $6.99"}
LABEL_SPEC = f"""Task: you are labeling real Reddit posts/comments written in the two weeks after Spotify announced a US Premium
price increase ({{prices}}).
Each row shows the thread title it was posted in, then the text. Label what the WRITER says, not what the thread says.

For every row write one JSON object with exactly these keys:
  "uid": copy the row's uid exactly
  "relevant": true if the writer is reacting to or discussing the price increase (directly or clearly by context), else false
  "sentiment": the writer's feeling about the price increase / Spotify, one of {SENTIMENTS}
  "action": one of {ACTIONS + ["none"]}
      ({ACTION_HELP}; none = no stance or intention stated: a question, information, a joke with no stance)
      Use "complain" for negative comments that do not say they will leave. Use "accept" for defending the price or
      saying they will keep paying. Only use cancel/switch/downgrade when the writer says they will or did do it.
  "switch_to": the service named if action is "switch", else null
  "themes": 0-3 items from this list only: {list(THEMES)}
Theme meanings: {json.dumps(THEMES)}
If relevant is false, still fill the other keys (use "none" and [] when nothing applies).

Write ONE JSON array (one object per row, same order) to the output file. Valid JSON only, no markdown fences."""


def raw_posts(event):
    """All post-event posts incl. short link-post titles (the >= 8-word filter drops e.g. "Spotify hikes U.S. Premium
    subscription price", which hid its whole comment thread). Returns post_id -> (title text, price_related)."""
    if event == "2023":
        c = pd.read_csv(HERE / "spotify_2023_corpus.csv", usecols=["kind", "post_id", "phase", "text", "price_related"])
        c = c[(c.kind == "post") & (c.phase == "post")]
        return c.set_index("post_id")[["text", "price_related"]]
    import build_spotify_corpus as B
    d = pd.read_json(HERE / "holdout_2026" / "post.jsonl", lines=True)
    d = d[d.kind == "post"]
    t = (d.title.fillna("") + " " + d.body.fillna("")).str.strip()
    return pd.DataFrame({"text": t.values, "price_related": t.str.contains(B.PRICE_RE).values}, index=d.id.values)


def real_rows(event):
    d = pd.read_csv(GT[event])
    u = d[d.lens == "users"]
    raw = raw_posts(event)
    hike = set(u[(u.kind == "post") & u.price_related].post_id) | set(raw[raw.price_related].index)
    sel = u[u.post_id.isin(hike) | u.price_related].copy()
    titles = pd.concat([raw.text, u[u.kind == "post"].set_index("post_id").text])
    titles = titles[~titles.index.duplicated()].str.slice(0, 120)
    sel["thread"] = sel.post_id.map(titles).fillna("(thread title unavailable)")
    sel["in_hike_thread"] = sel.post_id.isin(hike)
    return sel.sort_values("created_utc").reset_index(drop=True)


def prep_labels(event):
    root = HERE / f"eval_{event}" / "labels"
    (root / "briefs").mkdir(parents=True, exist_ok=True); (root / "out").mkdir(exist_ok=True)
    rows = real_rows(event)
    rows.to_csv(HERE / f"eval_{event}" / "real_rows.csv", index=False)
    done = set()
    for f in (root / "out").glob("*.json"):
        done |= {x["uid"] for x in json.loads(f.read_text())}
    todo = rows[~rows.uid.isin(done)]
    start = len(list((root / "briefs").glob("*.md"))) + 1 if done else 1
    batches = np.array_split(todo.sample(frac=1, random_state=7), max(1, int(np.ceil(len(todo) / BATCH))))
    for i, b in enumerate(batches, start):
        out = root / "out" / f"batch_{i:02d}.json"
        lines = [f"[uid={r.uid}] (thread: {re.sub(r'\s+', ' ', r.thread)}) {re.sub(r'\s+', ' ', r.text)[:600]}"
                 for r in b.itertuples()]
        (root / "briefs" / f"batch_{i:02d}.md").write_text(
            f"OUTPUT FILE: {out}\n\n{LABEL_SPEC.replace('{prices}', PRICES[event])}\n\nROWS ({len(b)}):\n" + "\n".join(lines) + "\n")
    print(f"{len(rows)} real rows, {len(todo)} unlabeled -> {len(batches)} new label briefs in {root / 'briefs'}")


def collect_labels(event):
    root = HERE / f"eval_{event}"
    rows = pd.read_csv(root / "real_rows.csv")
    labs, problems = [], []
    for f in sorted((root / "labels" / "out").glob("*.json")):
        try:
            labs += json.loads(f.read_text())
        except Exception as e:
            problems.append(f"{f.name}: {e}")
    L = pd.DataFrame(labs)
    bare = rows.set_index(rows.uid.str.split(":").str[-1]).uid      # a labeler may drop the "comment:"/"post:" prefix
    L["uid"] = L.uid.where(L.uid.isin(set(rows.uid)), L.uid.map(bare))
    L = L.dropna(subset=["uid"]).drop_duplicates("uid")
    L["themes"] = L.themes.apply(lambda t: "|".join(x for x in (t or []) if x in THEMES))
    bad = ~L.action.isin(ACTIONS + ["none"]) | ~L.sentiment.isin(SENTIMENTS)
    problems += [f"bad label {u}" for u in L[bad].uid]
    m = rows.merge(L, on="uid", how="left")
    missing = m.relevant.isna().sum()
    m.to_csv(root / "real_labels.csv", index=False)
    if (root / "handcheck_100.csv").exists():      # keep the sample that was already audited
        print(f"labeled {len(L)} / {len(rows)} rows, missing {missing}, problems {len(problems)} (hand-check sheet kept)")
        return
    hc = m[m.relevant.notna()].sample(100, random_state=11)
    hc = hc[["uid", "subreddit", "thread", "text", "relevant", "sentiment", "action", "themes"]].assign(
        ok_relevant="", ok_sentiment="", ok_action="", ok_themes="", note="")
    hc.to_csv(root / "handcheck_100.csv", index=False)
    print(f"labeled {len(L)} / {len(rows)} rows, missing {missing}, problems {len(problems)}")
    for p in problems[:20]:
        print(" ", p)
    print(f"hand-check sheet: {root / 'handcheck_100.csv'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["prep-labels", "collect-labels", "score"])
    ap.add_argument("--event", default="2023")
    a = ap.parse_args()
    if a.step == "prep-labels":
        prep_labels(a.event)
    elif a.step == "collect-labels":
        collect_labels(a.event)
    else:
        from score import score
        score(a.event)
