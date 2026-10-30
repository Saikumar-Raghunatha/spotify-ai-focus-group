#!/usr/bin/env python3
"""
Pull the Jan 2026 holdout data (r/spotify + r/truespotify) from the Arctic Shift archive.

    python holdout_2026_pull.py            # full pull (resumable)
    python holdout_2026_pull.py --test     # one-day check

Windows (UTC, end exclusive):
    pre  : 2024-11-24 .. 2025-11-24   persona source (stops before the FT leak on ~2025-11-25)
    post : 2026-01-15 .. 2026-01-31   ground truth (official announcement 2026-01-15, through 30 Jan)
    2025-11-24 .. 2026-01-14 is never pulled.

Writes holdout_2026/{pre,post}.jsonl plus a .done file per window so a re-run skips finished chunks.
SEALED: the post file must not be read or used for tuning until the 2023 pipeline is frozen.
"""
import json, sys, time, threading, urllib.parse, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent / "holdout_2026"
BASE = "https://arctic-shift.photon-reddit.com/api"
SUBS = ["spotify", "truespotify"]
UTC = timezone.utc
WINDOWS = {
    "pre": (datetime(2024, 11, 24, tzinfo=UTC), datetime(2025, 11, 24, tzinfo=UTC)),
    "post": (datetime(2026, 1, 15, tzinfo=UTC), datetime(2026, 1, 31, tzinfo=UTC)),
}
PAGE, PAUSE, CHUNK_DAYS = 100, 0.3, 7
lock = threading.Lock()


def get(url):
    err = None
    for i in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "class-project-research/1.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err = f"HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:200]}"
            if e.code in (400, 404):
                raise RuntimeError(err)
        except Exception as e:
            err = repr(e)
        time.sleep(3 * (i + 1))
    raise RuntimeError(f"gave up: {err}")


def ts_iso(t):
    return datetime.fromtimestamp(int(t), tz=UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def row(kind, r):
    perma = r.get("permalink") or ""
    return {
        "kind": kind, "id": r.get("id"),
        "postId": (r.get("link_id") or "").replace("t3_", "") if kind == "comment" else r.get("id"),
        "parentId": r.get("parent_id") or "", "subreddit": r.get("subreddit"),
        "created_utc": ts_iso(r["created_utc"]), "score": r.get("score"), "num_comments": r.get("num_comments"),
        "title": r.get("title") if kind == "post" else None,
        "body": (r.get("selftext") if kind == "post" else r.get("body")) or "",
        "author": r.get("author"),
        "permalink": ("https://www.reddit.com" + perma) if perma.startswith("/") else perma,
    }


def pull(kind, sub, start, end):
    ep = "posts/search" if kind == "post" else "comments/search"
    cur, stop, seen, rows = int(start.timestamp()), int(end.timestamp()), set(), []
    while cur < stop:
        q = urllib.parse.urlencode({"subreddit": sub, "after": cur, "before": stop, "sort": "asc", "limit": PAGE})
        data = get(f"{BASE}/{ep}?{q}").get("data", [])
        new = [r for r in data if r["id"] not in seen]
        for r in new:
            seen.add(r["id"]); rows.append(row(kind, r))
        if len(data) < PAGE:
            break
        last = int(data[-1]["created_utc"])
        cur = max(last - 1, cur) if new else last + 1
        time.sleep(PAUSE)
    return rows


def jobs(name):
    a, b = WINDOWS[name]
    for sub in SUBS:
        for kind in ("post", "comment"):
            s = a
            while s < b:
                e = min(s + timedelta(days=CHUNK_DAYS), b)
                yield sub, kind, s, e
                s = e


def run(name):
    OUT.mkdir(exist_ok=True)
    out, done = OUT / f"{name}.jsonl", OUT / f".done_{name}.txt"
    finished = set(done.read_text().split("\n")) if done.exists() else set()

    def work(job):
        sub, kind, s, e = job
        key = f"{sub}|{kind}|{s.date()}"
        if key in finished:
            return
        rows = pull(kind, sub, s, e)
        with lock:
            with open(out, "a", encoding="utf-8") as f:
                f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
            with open(done, "a") as d:
                d.write(key + "\n")
            print(f"[{name}] r/{sub} {kind}s {s.date()}..{e.date()}: {len(rows)}", flush=True)

    with ThreadPoolExecutor(4) as ex:
        list(ex.map(work, list(jobs(name))))
    print(f"done {name}: {out}", flush=True)


if __name__ == "__main__":
    if "--test" in sys.argv:
        s = WINDOWS["post"][0]
        for k in ("post", "comment"):
            print(k, len(pull(k, "spotify", s, s + timedelta(days=1))))
    else:
        for w in ("post", "pre"):
            run(w)
