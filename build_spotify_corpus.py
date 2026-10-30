#!/usr/bin/env python3
"""
Build one clean, labeled Reddit corpus for the Spotify price-hike back-test
(Task 1 = pre-event persona data, Task 2 = post-event ground truth).

Usage:
    export APIFY_TOKEN="apify_api_xxx"        # your Apify account token (optional if only using local Arctic Shift files)
    python build_spotify_corpus.py            # merges every source listed in manifest.json

Outputs (written next to this script):
    spotify_2023_corpus.csv      one row per post/comment, labeled by phase
    spotify_2023_corpus.jsonl    same data, one JSON object per line
    corpus_summary.json          row counts by phase / role / subreddit / kind

Why this exists: the Apify datasets are private to your account and expire
(unnamed datasets are kept ~7 days by default), so this script downloads them
once and merges them into a single file the other tasks can use.
"""
import csv, hashlib, json, os, re, sys, time, urllib.parse, urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIELDS = ("kind,id,postId,parentId,subreddit,created_utc,score,num_comments,depth,"
          "title,body,author,permalink,upvote_ratio,is_deleted_or_removed")

# ---- leakage rules (event 1: Spotify US price hike announced Mon 24 Jul 2023) ----
# A WSJ report leaked the hike on Fri 21 Jul 2023, so persona data stops BEFORE that.
CUTOFF_PRE_END   = datetime(2023, 7, 21, tzinfo=timezone.utc)   # pre  : created <  this
ANNOUNCEMENT     = datetime(2023, 7, 24, tzinfo=timezone.utc)   # post : created >= this
POST_WINDOW_END  = datetime(2023, 8, 8, tzinfo=timezone.utc)    # post : created <  this
PRE_WINDOW_START = datetime(2022, 7, 21, tzinfo=timezone.utc)   # pre  : created >= this

PRICE_RE   = re.compile(r"\b(price|prices|pricing|hike|increase|raise|raising|cost|costs|expensive|"
                        r"cheaper|cancel|cancell?ing|unsubscribe|subscription|worth it|\$\s?\d)", re.I)
SPOTIFY_RE = re.compile(r"spotify", re.I)
DELETED    = {"[deleted]", "[removed]", ""}


def use_event(event):
    """Set the leakage windows for an event from events.json (default 2023 values above stay if event == '2023')."""
    global CUTOFF_PRE_END, ANNOUNCEMENT, POST_WINDOW_END, PRE_WINDOW_START
    ev = json.loads((HERE / "events.json").read_text())[event]
    d = lambda x: datetime.fromisoformat(x).replace(tzinfo=timezone.utc)
    PRE_WINDOW_START, CUTOFF_PRE_END, ANNOUNCEMENT, POST_WINDOW_END = d(ev["pre_start"]), d(ev["cutoff"]), d(ev["announcement"]), d(ev["post_end"])


def parse_ts(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def phase_of(ts):
    if ts is None:
        return "unknown"
    if PRE_WINDOW_START <= ts < CUTOFF_PRE_END:
        return "pre"            # safe to build personas from
    if CUTOFF_PRE_END <= ts < ANNOUNCEMENT:
        return "leak_gap"       # leak -> announcement: do NOT use for personas or ground truth
    if ANNOUNCEMENT <= ts < POST_WINDOW_END:
        return "post"           # real reaction (ground truth)
    return "out_of_window"


def role_of(phase):
    return {"pre": "persona_source", "post": "ground_truth"}.get(phase, "excluded")


def hash_author(a):
    if not a or a in ("[deleted]", "AutoModerator"):
        return ""
    return hashlib.sha1(("spotify-poc|" + a).encode()).hexdigest()[:10]


def fetch_dataset(dataset_id, token, page=1000):
    rows, offset = [], 0
    while True:
        q = urllib.parse.urlencode({"token": token, "format": "json", "clean": "true",
                                    "fields": FIELDS, "offset": offset, "limit": page})
        url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?{q}"
        for attempt in range(4):
            try:
                with urllib.request.urlopen(url, timeout=120) as r:
                    batch = json.loads(r.read().decode("utf-8"))
                break
            except Exception as e:
                if attempt == 3:
                    raise
                time.sleep(2 * (attempt + 1))
        rows.extend(batch)
        if len(batch) < page:
            return rows
        offset += page


def clean_rows(raw_rows, source):
    out = []
    for r in raw_rows:
        kind = r.get("kind")
        title, body = (r.get("title") or "").strip(), (r.get("body") or "").strip()
        if kind == "post":
            text = (title + ("\n\n" + body if body not in DELETED else "")).strip()
        else:
            text = body
        if text in DELETED or (kind == "comment" and body in DELETED):
            continue
        ts = parse_ts(r.get("created_utc"))
        ph = phase_of(ts)
        out.append({
            "uid": f"{kind}:{r.get('id')}",
            "kind": kind,
            "reddit_id": r.get("id"),
            "post_id": r.get("postId") or (r.get("id") if kind == "post" else ""),
            "parent_id": r.get("parentId") or "",
            "subreddit": r.get("subreddit"),
            "created_utc": r.get("created_utc"),
            "phase": ph,
            "role": role_of(ph),
            "score": r.get("score"),
            "num_comments": r.get("num_comments"),
            "depth": r.get("depth"),
            "author_hash": hash_author(r.get("author")),   # usernames removed on purpose
            "text": text,
            "word_count": len(text.split()),
            "mentions_spotify": bool(SPOTIFY_RE.search(text)),
            "price_related": bool(PRICE_RE.search(text)),
            "permalink": r.get("permalink"),
            "source_dataset": source,
        })
    return out


def merge(all_rows):
    """Dedupe on uid, keep the first copy; drop rows whose own timestamp is unknown."""
    seen, merged = set(), []
    for r in all_rows:
        if r["uid"] in seen or r["phase"] == "unknown":
            continue
        seen.add(r["uid"])
        merged.append(r)
    return merged


def summarize(rows):
    return {
        "total_rows": len(rows),
        "by_phase": dict(Counter(r["phase"] for r in rows)),
        "by_role": dict(Counter(r["role"] for r in rows)),
        "by_kind": dict(Counter(r["kind"] for r in rows)),
        "top_subreddits_persona_source": Counter(r["subreddit"] for r in rows if r["role"] == "persona_source").most_common(15),
        "top_subreddits_ground_truth": Counter(r["subreddit"] for r in rows if r["role"] == "ground_truth").most_common(15),
        "persona_source_mentioning_spotify": sum(1 for r in rows if r["role"] == "persona_source" and r["mentions_spotify"]),
        "ground_truth_price_related": sum(1 for r in rows if r["role"] == "ground_truth" and r["price_related"]),
    }


def main():
    token = os.environ.get("APIFY_TOKEN")      # only needed for the Apify datasets; Arctic Shift files are local
    event = sys.argv[sys.argv.index("--event") + 1] if "--event" in sys.argv else "2023"
    use_event(event)
    suffix = "" if event == "2023" else f"_{event}"
    manifest = json.loads((HERE / ("manifest.json" if event == "2023" else f"manifest_{event}.json")).read_text())
    print(f"Event {event}: personas < {CUTOFF_PRE_END.date()} | gap until {ANNOUNCEMENT.date()} | ground truth until {POST_WINDOW_END.date()}")
    all_rows = []
    for d in manifest["datasets"]:
        if not d.get("use", True):
            continue
        if "path" in d:                                   # local JSONL (e.g. from arctic_shift_pull.py)
            p = HERE / d["path"]
            if not p.exists():
                print(f"Skipping {d['path']} (file not found yet)")
                continue
            print(f"Reading {d['path']}  ({d['label']}) ...", flush=True)
            raw = [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
        else:
            if not token:
                print(f"Skipping Apify dataset {d['id']} (no APIFY_TOKEN set)")
                continue
            print(f"Downloading {d['id']}  ({d['label']}) ...", flush=True)
            raw = fetch_dataset(d["id"], token)
        rows = clean_rows(raw, d["label"])
        print(f"   {len(raw)} raw -> {len(rows)} usable")
        all_rows.extend(rows)
    merged = merge(all_rows)

    cols = list(merged[0].keys())
    with open(HERE / f"spotify_{event}_corpus.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(merged)
    with open(HERE / f"spotify_{event}_corpus.jsonl", "w", encoding="utf-8") as f:
        for r in merged:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summ = summarize(merged)
    (HERE / f"corpus_summary{suffix}.json").write_text(json.dumps(summ, indent=2))
    print(json.dumps(summ, indent=2))


if __name__ == "__main__":
    main()
