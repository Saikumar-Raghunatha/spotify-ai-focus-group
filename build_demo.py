#!/usr/bin/env python3
"""Write deliverables/spotify_focus_group_demo.html from results.json (one self-contained page)."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = json.loads((HERE / "results.json").read_text())

keep = {}
for e, b in R["events"].items():
    conds = {k: {m: v[m] for m in ("action", "sentiment", "themes", "action_tvd", "sentiment_tvd", "theme_rho", "leave", "switch_to")}
             for k, v in b["conditions"].items() if k in ("rag", "plain", "norag", "rag_untuned")}
    keep[e] = {"announcement": b["announcement"], "date": b["date"], "quotes": b["quotes"],
               "real": {m: b["real"][m] for m in ("action", "sentiment", "themes", "leave", "n_opinion", "authors", "switch_to")},
               "conditions": conds,
               "personas": [{k: p[k] for k in ("id", "segment", "name", "label", "who", "price_sensitivity", "reasons_to_stay",
                                                "pain_points", "pool", "reactions")} for p in b["personas"]]}
data = json.dumps({"events": keep, "segments": R["segments"]}, ensure_ascii=False).replace("</", "<\\/")
html = (HERE / "demo_template.html").read_text().replace("__DATA__", data)
out = HERE / "deliverables" / "spotify_focus_group_demo.html"
out.write_text(html)
print("wrote", out, f"{len(html) / 1024:.0f} KB")
