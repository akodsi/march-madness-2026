"""
Community commentary pipeline.

Fetches team coverage from two public sources:
  1. Google News RSS — recent news headlines from reputable outlets
  2. Reddit r/collegebasketball — top community posts about each team

Both are summarized into plain-text strings and stored alongside the raw
items in community_2026.json. This file is merged into the commentary
dict at prediction time (see rule_engine._load_community).

Output: data/processed/community_2026.json
Structure per team:
{
    "Duke": {
        "google_news": [
            {"title": "...", "summary": "...", "source": "AP", "date": "..."}
        ],
        "google_news_summary": "Duke enters as the clear #1 seed...",
        "reddit_posts": [
            {"title": "...", "score": 412, "date": "..."}
        ],
        "reddit_summary": "Fan discussion centers on...",
        "last_updated": "2026-03-17"
    }
}
"""
from __future__ import annotations

import time
import json
import requests
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

# Reddit requires a descriptive User-Agent — plain Python UA gets 429s
REDDIT_HEADERS = {
    "User-Agent": "march-madness-predictor/1.0 (educational project; bracket analysis)"
}

MAX_NEWS_ITEMS   = 4
MAX_REDDIT_ITEMS = 5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_rss_date(date_str: str) -> str:
    """Convert RSS pubDate string to YYYY-MM-DD. Falls back to today."""
    today = str(date.today())
    if not date_str:
        return today
    # RSS dates are RFC 2822: "Mon, 17 Mar 2026 14:30:00 GMT"
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return today


def _parse_reddit_date(utc_ts: float) -> str:
    """Convert Unix UTC timestamp to YYYY-MM-DD."""
    try:
        return datetime.fromtimestamp(utc_ts, tz=timezone.utc).strftime("%Y-%m-%d")
    except Exception:
        return str(date.today())


def _summarize(titles: list[str], max_items: int = 3) -> str:
    """Join top N titles into a brief summary string."""
    items = [t.strip().rstrip(".") for t in titles[:max_items] if t.strip()]
    if not items:
        return ""
    return ". ".join(items) + "."


# ---------------------------------------------------------------------------
# Google News RSS
# ---------------------------------------------------------------------------

def _fetch_google_news(team_name: str) -> list[dict]:
    """
    Pull recent headlines from Google News RSS for a team.
    Query: "{team_name} basketball NCAA"
    """
    query = quote_plus(f'"{team_name}" basketball NCAA tournament 2026')
    url = (
        f"https://news.google.com/rss/search"
        f"?q={query}&hl=en-US&gl=US&ceid=US:en"
    )

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"    [Google News] fetch failed for {team_name}: {e}")
        return []

    items = []
    try:
        root = ET.fromstring(resp.content)
        channel = root.find("channel")
        if channel is None:
            return []

        for item in channel.findall("item")[:MAX_NEWS_ITEMS]:
            title   = (item.findtext("title") or "").strip()
            desc    = (item.findtext("description") or "").strip()
            pub     = item.findtext("pubDate") or ""
            source_el = item.find("source")
            source  = source_el.text.strip() if source_el is not None and source_el.text else "Google News"

            # Google News titles often have " - Source Name" appended — strip it
            # so we get a clean title, but preserve the source separately
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                title = parts[0].strip()
                if not source_el:
                    source = parts[1].strip()

            if title:
                items.append({
                    "title":   title,
                    "summary": desc[:200] if desc else "",
                    "source":  source,
                    "date":    _parse_rss_date(pub),
                })
    except ET.ParseError as e:
        print(f"    [Google News] XML parse error for {team_name}: {e}")

    return items


# ---------------------------------------------------------------------------
# Reddit r/collegebasketball
# ---------------------------------------------------------------------------

def _fetch_reddit_posts(team_name: str) -> list[dict]:
    """
    Pull top recent posts mentioning the team from r/collegebasketball.
    Uses Reddit's public JSON API — no authentication required.
    """
    query = quote_plus(f"{team_name} basketball")
    url = (
        "https://www.reddit.com/r/collegebasketball/search.json"
        f"?q={query}&sort=top&t=month&limit={MAX_REDDIT_ITEMS}&restrict_sr=1"
    )

    try:
        resp = requests.get(url, headers=REDDIT_HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"    [Reddit] fetch failed for {team_name}: {e}")
        return []

    posts = []
    try:
        children = data.get("data", {}).get("children", [])
        for child in children:
            post = child.get("data", {})
            title = (post.get("title") or "").strip()
            score = int(post.get("score") or 0)
            ts    = float(post.get("created_utc") or 0)

            if title:
                posts.append({
                    "title": title,
                    "score": score,
                    "date":  _parse_reddit_date(ts),
                })
    except Exception as e:
        print(f"    [Reddit] parse error for {team_name}: {e}")

    return posts


# ---------------------------------------------------------------------------
# Per-team entry builder
# ---------------------------------------------------------------------------

def fetch_team_community(team_name: str) -> dict:
    today = str(date.today())

    news  = _fetch_google_news(team_name)
    posts = _fetch_reddit_posts(team_name)

    news_summary   = _summarize([n["title"] for n in news])
    reddit_summary = _summarize([p["title"] for p in posts])

    return {
        "google_news":         news,
        "google_news_summary": news_summary,
        "reddit_posts":        posts,
        "reddit_summary":      reddit_summary,
        "last_updated":        today,
    }


# ---------------------------------------------------------------------------
# Batch runner
# ---------------------------------------------------------------------------

def fetch_all_community(teams: list[str], delay: float = 1.5) -> dict:
    """
    Fetch community data for all tournament teams.
    Delay is longer than ESPN fetches to respect Reddit rate limits.
    """
    print(f"  Fetching community data for {len(teams)} teams...")
    community = {}

    for i, team in enumerate(teams):
        entry = fetch_team_community(team)
        community[team] = entry

        news_count   = len(entry["google_news"])
        reddit_count = len(entry["reddit_posts"])
        print(
            f"    {team:25s}  "
            f"news={news_count}  reddit={reddit_count}"
        )

        if i < len(teams) - 1:
            time.sleep(delay)

        if (i + 1) % 10 == 0:
            print(f"    ... {i + 1}/{len(teams)} done")

    return community


def save_community(community: dict, year: int = 2026) -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    path = PROCESSED_DIR / f"community_{year}.json"
    with open(path, "w") as f:
        json.dump(community, f, indent=2)
    print(f"  Saved community → {path}  ({len(community)} teams)")
    return path


def load_community(year: int = 2026) -> dict:
    """Load saved community data. Returns empty dict if file doesn't exist."""
    path = PROCESSED_DIR / f"community_{year}.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


if __name__ == "__main__":
    from pipeline.tournament_filter import build_tournament_teams

    teams = build_tournament_teams()["Team"].tolist()
    community = fetch_all_community(teams, delay=1.5)
    save_community(community)

    total_news   = sum(len(c["google_news"])  for c in community.values())
    total_reddit = sum(len(c["reddit_posts"]) for c in community.values())
    print(f"\nTotal: {total_news} news items, {total_reddit} reddit posts across {len(community)} teams")
