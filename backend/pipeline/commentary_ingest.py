"""
Expert commentary / analysis pipeline.

Scrapes pre-tournament analysis and news for each team from ESPN's public API.
Stores structured commentary in a JSON file that the frontend can display in
the matchup detail modal.

Sources:
  1. ESPN team news — headlines + summaries from ESPN's team page API
  2. ESPN team record/standing context — conference, ranking, streak

This is a DISPLAY-ONLY enrichment layer. Commentary is NOT fed into the
weighted prediction formula — it's shown alongside the signal breakdown
so the user gets a sense check from expert sources.

Output: data/processed/commentary_2026.json
Structure:
{
    "Duke": {
        "headlines": [
            {"title": "...", "summary": "...", "source": "ESPN", "date": "..."}
        ],
        "team_context": "...",      # e.g. "ACC champion, 32-2, ranked #1"
        "sentiment": "positive",    # basic: positive / neutral / negative
        "last_updated": "2026-03-16"
    }
}
"""
from __future__ import annotations

import time
import json
import requests
from datetime import date
from pathlib import Path

from pipeline.espn_ids import ESPN_TEAM_IDS, espn_summary_url

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

# Simple keyword-based sentiment heuristic
POSITIVE_KEYWORDS = [
    "dominant", "impressive", "elite", "strong", "champion", "contender",
    "historic", "unbeaten", "surge", "hot streak", "winning streak",
    "breakthrough", "stellar", "outstanding", "powerhouse", "favorite",
    "cruised", "rolled", "blowout win", "commanding",
]
NEGATIVE_KEYWORDS = [
    "struggling", "upset", "collapse", "injury", "loss", "losing streak",
    "inconsistent", "slump", "eliminated", "underperforming", "disappointing",
    "suspension", "concern", "troubled", "limping", "vulnerable",
    "blown lead", "choked", "fell apart",
]


def _basic_sentiment(text: str) -> str:
    """
    Dead-simple keyword sentiment. Not meant to be precise —
    just a qualitative indicator for the UI.
    """
    text_lower = text.lower()
    pos = sum(1 for kw in POSITIVE_KEYWORDS if kw in text_lower)
    neg = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text_lower)

    if pos > neg + 1:
        return "positive"
    elif neg > pos + 1:
        return "negative"
    return "neutral"


def _fetch_team_news(team_name: str) -> dict | None:
    """
    Fetch ESPN team summary which includes news headlines and team context.
    """
    url = espn_summary_url(team_name)
    if not url:
        return None

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"    ESPN summary fetch failed for {team_name}: {e}")
        return None


def scrape_team_commentary(team_name: str) -> dict:
    """
    Build commentary entry for a team from ESPN data.
    """
    data = _fetch_team_news(team_name)
    today = str(date.today())

    entry = {
        "headlines": [],
        "team_context": "",
        "sentiment": "neutral",
        "last_updated": today,
    }

    if data is None:
        return entry

    # Extract team context (record, standing, conference)
    team_info = data.get("team", {})
    record_items = team_info.get("record", {}).get("items", [])
    if record_items:
        overall = record_items[0]
        record_str = overall.get("summary", "")
        stats = overall.get("stats", [])
        # Pull win-loss from stats if available
        context_parts = []
        if record_str:
            context_parts.append(record_str)

        # Conference
        conf_groups = team_info.get("groups", {})
        if conf_groups:
            conf_name = conf_groups.get("name", "")
            if conf_name:
                context_parts.append(conf_name)

        # Ranking
        rank = team_info.get("rank", 0)
        if rank and rank > 0:
            context_parts.append(f"Ranked #{rank}")

        entry["team_context"] = " · ".join(context_parts)

    # Extract news headlines
    news = data.get("news", {}).get("articles", [])
    if not news:
        # Try alternate structure
        news = data.get("news", {}).get("items", [])

    all_text = ""
    for article in news[:5]:  # Cap at 5 headlines
        headline = {
            "title": article.get("headline", article.get("title", "")),
            "summary": article.get("description", article.get("summary", "")),
            "source": "ESPN",
            "date": article.get("published", today),
        }
        if headline["title"]:
            entry["headlines"].append(headline)
            all_text += f" {headline['title']} {headline['summary']}"

    # Add team context to sentiment analysis text
    all_text += f" {entry['team_context']}"
    entry["sentiment"] = _basic_sentiment(all_text)

    return entry


def fetch_all_commentary(teams: list[str], delay: float = 0.5) -> dict:
    """
    Fetch commentary for all tournament teams.
    Returns dict of {team_name: commentary_entry}.
    """
    print(f"  Fetching commentary for {len(teams)} teams...")
    commentary = {}

    for i, team in enumerate(teams):
        entry = scrape_team_commentary(team)
        commentary[team] = entry

        headline_count = len(entry["headlines"])
        sentiment = entry["sentiment"]
        ctx = entry["team_context"][:50] if entry["team_context"] else "(no context)"
        print(f"    {team:25s}  {headline_count} headlines  {sentiment:8s}  {ctx}")

        if i < len(teams) - 1:
            time.sleep(delay)

        if (i + 1) % 10 == 0:
            print(f"    ... {i + 1}/{len(teams)} done")

    return commentary


def save_commentary(commentary: dict, year: int = 2026) -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    path = PROCESSED_DIR / f"commentary_{year}.json"
    with open(path, "w") as f:
        json.dump(commentary, f, indent=2)
    print(f"  Saved commentary → {path}  ({len(commentary)} teams)")
    return path


def load_commentary(year: int = 2026) -> dict:
    """Load saved commentary data. Returns empty dict if file doesn't exist."""
    path = PROCESSED_DIR / f"commentary_{year}.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


if __name__ == "__main__":
    from pipeline.tournament_filter import build_tournament_teams

    teams = build_tournament_teams()["Team"].tolist()
    commentary = fetch_all_commentary(teams, delay=0.5)
    save_commentary(commentary)

    print("\nSentiment summary:")
    for sentiment in ["positive", "neutral", "negative"]:
        count = sum(1 for c in commentary.values() if c["sentiment"] == sentiment)
        teams_list = [t for t, c in commentary.items() if c["sentiment"] == sentiment]
        print(f"  {sentiment:10s}: {count} teams")
        if teams_list:
            print(f"    {', '.join(teams_list[:8])}")
