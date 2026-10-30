#!/usr/bin/env python3
"""
Pull the FULL history of r/spotify and r/truespotify from the Arctic Shift archive
(free, no login) for the July 2023 price-hike back-test.

    python arctic_shift_pull.py --test                 # 30-second check (July 2023 event)
    python arctic_shift_pull.py                        # full pull, July 2023
    python arctic_shift_pull.py --event 2026 --test    # check the Jan 2026 holdout window
    python arctic_shift_pull.py --event 2026           # full pull, Jan 2026 holdout

Writes, next to this script (same field names the rest of the pipeline already uses):
    arctic_spotify_pre.jsonl / arctic_spotify_post.jsonl            (2023)
    arctic_spotify_2026_pre.jsonl / arctic_spotify_2026_post.jsonl  (2026 holdout)
Dates for each event live in events.json.

Safe to stop and re-run: finished windows are skipped. Needs only Python 3 (no installs).
"""
import json, sys, time, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = "https://arctic-shift.photon-reddit.com/api"
SUBS = ["spotify", "truespotify"]
def load_windows(event):
    ev = json.loads((HERE / "events.json").read_text())[event]
    d = lambda x: datetime.fromisoformat(x).replace(tzinfo=timezone.utc)
    return {"pre": (d(ev["pre_start"]), d(ev["cutoff"])), "post": (d(ev["announcement"]), d(ev["post_end"]))}


PAGE = 100
PAUSE = 0.4          # seconds between requests (be polite to a free service)
CHUNK_DAYS = 7       # each sub-window is pulled separately so one failure never loses everything


def fetch_json(url):
    last = None
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "class-project-research/1.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")[:300]
            last = f"HTTP {e.code}: {body}"
            if e.code in (400, 404):                 # our request is wrong; retrying won't help
                raise RuntimeError(last)
        except Exception as e:
            last = repr(e)
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Gave up after retries. Last error: {last}")


def iso(ts):
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return str(ts)


def epoch(ts):
    if isinstance(ts, (int, float)):
        return int(ts)
    return int(datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp())


def normalize(kind, r):
    pid = (r.get("link_id") or "").replace("t3_", "") if kind == "comment" else r.get("id")
    perma = r.get("permalink") or ""
    if perma.startswith("/"):
        perma = "https://www.reddit.com" + perma
    return {
        "kind": kind, "id": r.get("id"), "postId": pid, "parentId": r.get("parent_id") or "",
        "subreddit": r.get("subreddit"), "created_utc": iso(r.get("created_utc")),
        "score": r.get("score"), "num_comments": r.get("num_comments"), "depth": None,
        "title": r.get("title") if kind == "post" else None,
        "body": (r.get("selftext") or "") if kind == "post" else (r.get("body") or ""),
        "author": r.get("author"), "permalink": perma, "upvote_ratio": r.get("upvote_ratio"),
        "is_deleted_or_removed": bool(r.get("removed_by_category")) if kind == "post" else False,
    }


def pull_window(kind, sub, start, end, fetch=fetch_json):
    """Page through [start, end) oldest-first, 100 rows at a time."""
    endpoint = "posts/search" if kind == "post" else "comments/search"
    seen, rows = set(), []
    cursor = int(start.timestamp())
    end_ts = int(end.timestamp())
    while cursor < end_ts:
        q = urllib.parse.urlencode({"subreddit": sub, "after": cursor, "before": end_ts,
                                    "sort": "asc", "limit": PAGE})
        data = fetch(f"{BASE}/{endpoint}?{q}").get("data", [])
        new = [r for r in data if r.get("id") not in seen]
        for r in new:
            seen.add(r["id"])
            rows.append(normalize(kind, r))
        if len(data) < PAGE:
            break
        last = epoch(data[-1]["created_utc"])
        if new:
            cursor = max(last - 1, cursor)    # overlap by 1 second so same-second rows are never missed; dupes dropped by id
        else:
            print(f"   warning: >{PAGE} rows share the second {last}; skipping ahead (a few rows may be missed)")
            cursor = last + 1
        time.sleep(PAUSE)
    return rows


def chunks(start, end):
    s = start
    while s < end:
        e = min(s + timedelta(days=CHUNK_DAYS), end)
        yield s, e
        s = e


def tag(event, name):
    return name if event == "2023" else f"{event}_{name}"      # 2023 keeps its original file names


def run_full(event):
    for name, (a, b) in load_windows(event).items():
        out = HERE / f"arctic_spotify_{tag(event, name)}.jsonl"
        done = HERE / f".done_{tag(event, name)}.txt"
        finished = set(done.read_text().split("\n")) if done.exists() else set()
        with open(out, "a", encoding="utf-8") as f:
            for sub in SUBS:
                for kind in ("post", "comment"):
                    for s_, e_ in chunks(a, b):
                        key = f"{sub}|{kind}|{s_.date()}"
                        if key in finished:
                            continue
                        rows = pull_window(kind, sub, s_, e_)
                        for r in rows:
                            f.write(json.dumps(r, ensure_ascii=False) + "\n")
                        f.flush()
                        with open(done, "a") as d:
                            d.write(key + "\n")
                        print(f"[{event}/{name}] r/{sub} {kind}s {s_.date()} -> {e_.date()}: {len(rows)} rows", flush=True)
        print(f"Finished {name}: {out}")


def run_test(event):
    print(f"Testing Arctic Shift for event {event} ...")
    s_ = load_windows(event)["post"][0]
    e_ = s_ + timedelta(days=1)
    for kind in ("post", "comment"):
        rows = pull_window(kind, "spotify", s_, e_)
        print(f"  r/spotify {kind}s on {s_.date()}: {len(rows)} rows")
        if rows:
            r = rows[0]
            print("   sample:", r["created_utc"], (r["title"] or r["body"] or "")[:80].replace("\n", " "))
    print("If both counts are above 0 and dates look right, run the full pull (no --test).")


if __name__ == "__main__":
    ev = sys.argv[sys.argv.index("--event") + 1] if "--event" in sys.argv else "2023"
    try:
        run_test(ev) if "--test" in sys.argv else run_full(ev)
    except RuntimeError as err:
        sys.exit(f"\nFAILED: {err}\nCopy this message and send it to Claude.")
