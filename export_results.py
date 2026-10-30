#!/usr/bin/env python3
"""
Collect every number the slides and the demo page show into one file: results.json.
Run after `python evaluate.py score --event 2023` and `--event 2026`.
"""
import json, re
from pathlib import Path
import pandas as pd
from simulate import ACTIONS, SENTIMENTS, THEMES, ANNOUNCEMENTS
from score import dist, theme_share, tvd, COMMUNITY, SENT_SCORE, CONDITIONAL

HERE = Path(__file__).resolve().parent
SEG_NAMES = {"0": "UI-update resisters", "1": "Premium value judges", "2": "Library power users",
             "3": "Podcast-flooded listeners", "4": "Genre & artist talk (not simulated)", "5": "Disillusioned comparers"}


def sims(event):
    """Conditions shown: tuned personas (with/without retrieval), untuned (2023 only), plain prompt."""
    out = {}
    if event == "2023":
        v1 = pd.read_csv(HERE / "sim_2023" / "results.csv")
        v2 = pd.read_csv(HERE / "sim_2023_v2" / "results.csv")
        out = {"rag": v2[v2.condition == "rag"], "norag": v2[v2.condition == "norag"],
               "rag_untuned": v1[v1.condition == "rag"], "plain": v1[v1.condition == "plain"]}
    else:
        s = pd.read_csv(HERE / "sim_2026" / "results.csv")
        out = {c: s[s.condition == c] for c in ("rag", "norag", "plain")}
    return out


def block(g, real_act, real):
    leave = g.action.isin(["cancel", "switch", "downgrade"])
    per_rep = [tvd(dist(x.action, ACTIONS), dist(real_act.action, ACTIONS)) for _, x in g.groupby("rep")]
    return {
        "n": int(len(g)),
        "action": dist(g.action, ACTIONS).round(4).to_dict(),
        "sentiment": dist(g.sentiment, SENTIMENTS).round(4).to_dict(),
        "themes": theme_share(g.themes).round(4).to_dict(),
        "action_tvd": round(tvd(dist(g.action, ACTIONS), dist(real_act.action, ACTIONS)), 4),
        "action_tvd_sd": round(float(pd.Series(per_rep).std()), 3),
        "sentiment_tvd": round(tvd(dist(g.sentiment, SENTIMENTS), dist(real_act.sentiment, SENTIMENTS)), 4),
        "theme_rho": round(float(pd.Series(theme_share(g.themes).values).corr(
            pd.Series(theme_share(real_act.themes).values), method="spearman")), 3),
        "leave": round(float(leave.mean()), 4),
        "leave_firm": round(float((leave & ~g.comment.str.contains(CONDITIONAL, case=False, regex=True)).mean()), 4),
        "mean_sentiment": round(float(g.sentiment.map(SENT_SCORE).mean()), 3),
        "switch_to": g[g.action == "switch"].switch_to.value_counts().head(5).to_dict(),
    }


def event_block(event):
    lab = pd.read_csv(HERE / f"eval_{event}" / "real_labels.csv")
    real = lab[(lab.relevant == True) & lab.subreddit.isin(COMMUNITY)]
    real_act = real[real.action != "none"]
    pdir = {"2023": "personas_v2", "2026": "personas_2026"}[event]
    personas = json.loads((HERE / pdir / "personas.json").read_text())["personas"]
    S = sims(event)
    leave = real_act.action.isin(["cancel", "switch", "downgrade"])
    real_b = {"n_labeled": int(len(lab)), "n_relevant": int(len(real)), "n_opinion": int(len(real_act)),
              "authors": int(real.author_hash.nunique()),
              "action": dist(real_act.action, ACTIONS).round(4).to_dict(),
              "sentiment": dist(real_act.sentiment, SENTIMENTS).round(4).to_dict(),
              "themes": theme_share(real_act.themes).round(4).to_dict(),
              "leave": round(float(leave.mean()), 4), "leave_firm": round(float(leave.mean()), 4),
              "mean_sentiment": round(float(real_act.sentiment.map(SENT_SCORE).mean()), 3),
              "switch_to": real_act[real_act.action == "switch"].switch_to.value_counts().head(5).to_dict()}
    # a few short real quotes per action (public Reddit text, authors never stored)
    quotes = {}
    for a in ["cancel", "switch", "complain", "accept"]:
        q = real_act[(real_act.action == a) & real_act.text.str.len().between(60, 260)].sample(
            frac=1, random_state=3).text.head(3)
        quotes[a] = [re.sub(r"\s+", " ", t) for t in q]
    # persona cards + their simulated comments (tuned personas, with retrieval)
    rag = S["rag"]
    cards = []
    for p in personas:
        pr = p["profile"]
        mine = rag[rag.id == p["persona_id"]].sort_values("rep")
        cards.append({
            "id": p["persona_id"], "segment": p["segment"], "focus": p["focus"], "pool": p["pool_rows"],
            "name": pr.get("name"), "label": pr.get("label"), "who": pr.get("who"),
            "price_sensitivity": pr.get("price_sensitivity"), "reasons_to_stay": pr.get("reasons_to_stay"),
            "pain_points": pr.get("pain_points", []), "likes": pr.get("likes", []),
            "alternatives": pr.get("alternatives_mentioned", []),
            "reactions": [{"rep": int(r.rep), "comment": r.comment, "action": r.action, "sentiment": r.sentiment,
                           "switch_to": r.switch_to if isinstance(r.switch_to, str) else None,
                           "themes": [t for t in str(r.themes).split("|") if t in THEMES]} for r in mine.itertuples()],
        })
    return {"announcement": ANNOUNCEMENTS[event]["text"], "date": ANNOUNCEMENTS[event]["date"], "real": real_b,
            "conditions": {k: block(g, real_act, real) for k, g in S.items()}, "quotes": quotes, "personas": cards}


def main():
    seg23 = pd.read_csv(HERE / "persona_sample_segmented.csv", usecols=["segment_id"]).segment_id.astype(str)
    seg26 = pd.read_csv(HERE / "persona_sample_segmented_2026.csv", usecols=["segment_id"]).segment_id.astype(str)
    out = {
        "labels": {"actions": ACTIONS, "sentiments": SENTIMENTS, "themes": THEMES},
        "segments": {k: {"name": v, "share_2023": round(float((seg23 == k).mean()), 4),
                         "share_2026": round(float((seg26 == k).mean()), 4)} for k, v in SEG_NAMES.items()},
        "events": {e: event_block(e) for e in ("2023", "2026")},
    }
    (HERE / "results.json").write_text(json.dumps(out, indent=1, default=str))
    for e, b in out["events"].items():
        print(e, {k: (v["action_tvd"], v["leave"], v["theme_rho"]) for k, v in b["conditions"].items()},
              "real leave", b["real"]["leave"])


if __name__ == "__main__":
    main()
