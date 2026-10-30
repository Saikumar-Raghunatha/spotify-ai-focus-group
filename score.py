#!/usr/bin/env python3
"""
TASK 6 scoring: compare simulated vs real reaction. Called by `python evaluate.py score [--event 2023]`.

Real side  = labeled rows from r/spotify + r/truespotify that the labeler marked relevant to the price increase.
Sim side   = sim_<event>/results.csv (rag, norag, plain; 5 reps x 26 each).

Metrics (lower TVD = closer; TVD is total variation distance between two distributions, 0..1):
    action TVD      real rows with a stated action (not "none") vs simulated actions
    sentiment TVD   + mean sentiment score (very_negative -2, negative -1, neutral 0, positive +1)
    themes          Spearman rank correlation of theme shares, and overlap of the top-5 themes
    noise floor     the same TVDs between two random halves of the real data (how close is "as close as it gets")
    hindsight       share of simulated comments using post-announcement knowledge cues
Writes eval_<event>/report.md, metrics.csv and fig_*.png.
"""
import re
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from simulate import ACTIONS, SENTIMENTS, THEMES

HERE = Path(__file__).resolve().parent
COMMUNITY = {"spotify", "truespotify"}
SENT_SCORE = {"very_negative": -2, "negative": -1, "neutral": 0, "positive": 1}
CONDS = ["rag", "norag", "plain"]
CONDITIONAL = r"\bif\b|\bunless\b|might|probably|thinking about|considering|one more"
COND_NAME = {"real": "Real community", "rag": "Personas + retrieval", "norag": "Personas, no retrieval",
             "plain": "Plain prompt", "rag_v2": "Tuned personas + retrieval", "norag_v2": "Tuned personas, no retrieval"}
# light-mode categorical slots from the dataviz reference palette; Real is drawn in neutral ink as the reference
COLORS = {"real": "#52514e", "rag": "#2a78d6", "norag": "#1baf7a", "plain": "#eb6834",
          "rag_v2": "#6250d6", "norag_v2": "#e87ba4"}
HINDSIGHT = {
    "repeat hike ('again', 'another hike')": r"(rais\w*|price\w*|hike\w*|increas\w*|going up)\W+(\w+\W+){0,3}again|another (price )?(hike|increase)|again\W+(\w+\W+){0,2}(rais|hike|price)",
    "market reaction (stock, investors)": r"\bstock\b(?! music)|\bshares\b|investor|wall street|earnings",
    "later prices ($11.99 / $12.99)": r"11\.99|12\.99",   # 2026: replaced by $13.99+ in score() (2024 hike is real history)
    "social backlash (twitter, trending)": r"twitter|\bX\b|trending|backlash|everyone is (cancel|leav)",
}


def dist(series, cats):
    return series.value_counts(normalize=True).reindex(cats, fill_value=0.0)


def theme_share(themes, cats=list(THEMES)):
    t = themes.fillna("").str.split("|")
    return pd.Series({c: t.apply(lambda v: c in v).mean() for c in cats})


def tvd(p, q):
    return 0.5 * float(np.abs(p.values - q.values).sum())


def score(event="2023"):
    root = HERE / f"eval_{event}"
    real_all = pd.read_csv(root / "real_labels.csv")
    real = real_all[(real_all.relevant == True) & real_all.subreddit.isin(COMMUNITY)].copy()
    real_act = real[real.action != "none"]
    sim = pd.read_csv(HERE / f"sim_{event}" / "results.csv")
    v2 = HERE / f"sim_{event}_v2" / "results.csv"          # tuning round: same conditions, rebalanced personas
    if v2.exists():
        t = pd.read_csv(v2); t["condition"] = t.condition + "_v2"
        sim = pd.concat([sim, t], ignore_index=True)
    CONDS[:] = [c for c in ["rag_v2", "norag_v2", "rag", "norag", "plain"] if c in set(sim.condition)]

    # like-for-like: every simulated response is an opinion, so the real side is the rows that state a stance/action
    A = {"real": dist(real_act.action, ACTIONS)}
    S = {"real": dist(real_act.sentiment, SENTIMENTS)}
    T = {"real": theme_share(real_act.themes)}
    for c in CONDS:
        g = sim[sim.condition == c]
        A[c], S[c], T[c] = dist(g.action, ACTIONS), dist(g.sentiment, SENTIMENTS), theme_share(g.themes)

    # split-half noise floor on the real side (200 random splits)
    rng = np.random.default_rng(0)
    floor = {"action": [], "sentiment": []}
    for _ in range(200):
        m = rng.random(len(real)) < 0.5
        a, b = real_act[m[:len(real_act)]], real_act[~m[:len(real_act)]]
        floor["action"].append(tvd(dist(a.action, ACTIONS), dist(b.action, ACTIONS)))
        floor["sentiment"].append(tvd(dist(a.sentiment, SENTIMENTS), dist(b.sentiment, SENTIMENTS)))

    rows = []
    real_top5 = set(T["real"].nlargest(5).index)
    for c in CONDS:
        g = sim[sim.condition == c]
        per_rep_a = [tvd(dist(x.action, ACTIONS), A["real"]) for _, x in g.groupby("rep")]
        per_rep_s = [tvd(dist(x.sentiment, SENTIMENTS), S["real"]) for _, x in g.groupby("rep")]
        rho = spearmanr(T[c].values, T["real"].values).statistic
        rows.append({
            "condition": c,
            "action_TVD": tvd(A[c], A["real"]), "action_TVD_rep_sd": np.std(per_rep_a, ddof=1),
            "sentiment_TVD": tvd(S[c], S["real"]), "sentiment_TVD_rep_sd": np.std(per_rep_s, ddof=1),
            "mean_sentiment_sim": g.sentiment.map(SENT_SCORE).mean(),
            "theme_spearman": rho, "top5_theme_overlap": len(real_top5 & set(T[c].nlargest(5).index)),
            "leave_rate_sim": g.action.isin(["cancel", "switch", "downgrade"]).mean(),
            # the real labeler counts "if X, I'll leave" as complain; apply the same rule to simulated comments
            "leave_rate_sim_firm": (g.action.isin(["cancel", "switch", "downgrade"])
                                    & ~g.comment.str.contains(CONDITIONAL, case=False, regex=True)).mean(),
        })
    M = pd.DataFrame(rows)
    M["mean_sentiment_real"] = real_act.sentiment.map(SENT_SCORE).mean()
    M["leave_rate_real"] = real_act.action.isin(["cancel", "switch", "downgrade"]).mean()
    M.to_csv(root / "metrics.csv", index=False)

    # hindsight cues: simulated comments vs the real posts (reference rate)
    cues = dict(HINDSIGHT)
    if event == "2026":   # earlier hikes are real history in 2026; only knowledge of the reaction or later prices counts
        cues.pop("repeat hike ('again', 'another hike')")
        cues.pop("later prices ($11.99 / $12.99)")
        cues["later prices ($13.99+)"] = r"13\.99|14\.99"
        cues["the November FT leak"] = r"financial times|\bFT\b|leaked|reported (back )?in november"
    H = []
    for name, rx in cues.items():
        r = {"cue": name}
        for c in CONDS:
            r[c] = sim[sim.condition == c].comment.str.contains(rx, case=False, regex=True).mean()
        r["real"] = real.text.str.contains(rx, case=False, regex=True).mean()
        H.append(r)
    H = pd.DataFrame(H)
    hits = sim[sim.comment.str.contains("|".join(f"(?:{v})" for v in cues.values()), case=False, regex=True)]

    figs = charts(root, A, S, T)
    report(root, event, real_all, real, real_act, sim, A, S, T, M, floor, H, hits, figs)
    print((root / "report.md").read_text())


def charts(root, A, S, T):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 10, "axes.edgecolor": "#c3c2b7", "axes.labelcolor": "#52514e",
                         "xtick.color": "#52514e", "ytick.color": "#52514e", "font.family": "sans-serif"})
    keys = ["real"] + CONDS
    out = []
    for name, D, cats, title in (
            ("action", A, ACTIONS, "What people say they will do (share of responses with a stated action)"),
            ("sentiment", S, SENTIMENTS, "Sentiment toward the price increase"),
            ("themes", T, list(THEMES), "Share of responses raising each theme")):
        order = cats if name != "themes" else list(T["real"].sort_values().index)
        fig, ax = plt.subplots(figsize=(8, 0.42 * len(order) * 1.6 + 1.2))
        h = 0.8 / len(keys)
        y = np.arange(len(order))
        for i, k in enumerate(keys):
            vals = D[k].reindex(order).values
            ax.barh(y + (len(keys) - 1 - i) * h - 0.4 + h / 2, vals, height=h * 0.86, color=COLORS[k], label=COND_NAME[k])
        ax.set_yticks(y); ax.set_yticklabels([o.replace("_", " ") for o in order])
        ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
        ax.grid(axis="x", color="#e6e5e0", linewidth=0.8); ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.set_title(title, loc="left", fontsize=11, color="#0b0b0b")
        ax.legend(frameon=False, loc="lower right", fontsize=9)
        fig.tight_layout()
        p = root / f"fig_{name}.png"
        fig.savefig(p, dpi=160, facecolor="#fcfcfb"); plt.close(fig)
        out.append(p.name)
    return out


def pct(x):
    return f"{x:.0%}"


def row(name, cells, floor=""):
    return f"| {name} | " + " | ".join(cells) + f" | {floor} |"


def report(root, event, real_all, real, real_act, sim, A, S, T, M, floor, H, hits, figs):
    tab = lambda D, cats: pd.DataFrame({COND_NAME[k]: D[k].reindex(cats).map(pct) for k in ["real"] + CONDS}).to_markdown()
    m = M.set_index("condition")
    L = [f"# Simulated vs real reaction ({event})\n",
         f"Real side: {len(real_all):,} labeled post-event rows; {len(real):,} are relevant reactions in r/spotify + "
         f"r/truespotify ({real.author_hash.nunique():,} authors); {len(real_act):,} express a stance or action and are the "
         f"comparison set (the other {len(real) - len(real_act):,} are questions or information; including them, real "
         f"sentiment is {dist(real.sentiment, SENTIMENTS).map(pct).to_dict()}). "
         f"Sim side: {len(sim)} responses ({len(CONDS)} conditions x 5 repetitions; 26 personas in v1, "
         f"{sim[sim.condition == CONDS[0]].groupby('rep').size().iloc[0]} in v2).\n",
         "## Scorecard\n",
         "| | " + " | ".join(COND_NAME[c] for c in CONDS) + " | Real-data noise floor |",
         "|---|" + "---|" * (len(CONDS) + 1),
         row("Action TVD (lower = closer)", [f"{m.action_TVD[c]:.2f} ± {m.action_TVD_rep_sd[c]:.2f}" for c in CONDS], f"{np.mean(floor['action']):.2f}"),
         row("Sentiment TVD", [f"{m.sentiment_TVD[c]:.2f} ± {m.sentiment_TVD_rep_sd[c]:.2f}" for c in CONDS], f"{np.mean(floor['sentiment']):.2f}"),
         row("Theme rank correlation (Spearman, higher = closer)", [f"{m.theme_spearman[c]:.2f}" for c in CONDS]),
         row("Top-5 themes shared with real", [f"{m.top5_theme_overlap[c]}/5" for c in CONDS]),
         row(f"Mean sentiment (real {m.mean_sentiment_real.iloc[0]:+.2f})", [f"{m.mean_sentiment_sim[c]:+.2f}" for c in CONDS]),
         row(f"Accept / defend (real {pct(A['real']['accept'])})", [pct(A[c]['accept']) for c in CONDS]),
         row(f"Positive sentiment (real {pct(S['real']['positive'])})", [pct(S[c]['positive']) for c in CONDS]),
         row(f"Leave rate: cancel+switch+downgrade (real {pct(m.leave_rate_real.iloc[0])})", [pct(m.leave_rate_sim[c]) for c in CONDS]),
         row("Leave rate, firm statements only (conditional threats counted as complain, as the real labeler did)", [pct(m.leave_rate_sim_firm[c]) for c in CONDS]),
         "\n± is the sd of the TVD across the 5 repetitions. The noise floor is the average TVD between two random halves "
         "of the real data: a simulation cannot be expected to beat it.\n",
         "## Actions\n", tab(A, ACTIONS), f"\n![actions]({figs[0]})\n",
         "## Sentiment\n", tab(S, SENTIMENTS), f"\n![sentiment]({figs[1]})\n",
         "## Themes\n", tab(T, list(T['real'].sort_values(ascending=False).index)), f"\n![themes]({figs[2]})\n",
         "## Switch targets\n",
         pd.DataFrame({"Real": real_act[real_act.action == 'switch'].switch_to.value_counts().head(5).to_dict(),
                       **{COND_NAME[c]: sim[(sim.condition == c) & (sim.action == 'switch')].switch_to.value_counts().head(5).to_dict() for c in CONDS}}).fillna(0).astype(int).to_markdown(),
         "\n## Hindsight-leakage check\n",
         "Share of comments containing cues that need knowledge from after the announcement. The real column is a "
         "reference only (real users legitimately knew these things).\n",
         H.rename(columns=COND_NAME).set_index("cue").map(pct).to_markdown(),
         "\nFlagged simulated comments:\n"]
    L += [f"- `{r.condition} r{r.rep} {r.id}`: {r.comment[:200]}" for r in hits.itertuples()]
    (root / "report.md").write_text("\n".join(L) + "\n")
