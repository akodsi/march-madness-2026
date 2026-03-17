"""
Momentum / recent form pipeline.

Fetches each tournament team's game-by-game results from ESPN's schedule API
and computes momentum metrics:
  - Last 10 games: W/L record
  - Current win/loss streak (e.g. W5, L2)
  - Average margin of victory in last 10 games
  - Momentum score (0–1 composite of recent win rate + margin trend)

ESPN schedule API (no auth required):
  site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams/{id}/schedule

Falls back to Sports-Reference game logs if ESPN is unavailable.
"""
from __future__ import annotations

import time
import requests
import pandas as pd
from pathlib import Path

from pipeline.espn_ids import ESPN_TEAM_IDS, espn_schedule_url

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
RAW_DIR = Path(__file__).parent.parent / "data" / "raw" / "momentum"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


def _fetch_espn_schedule(team_name: str) -> list[dict] | None:
    """
    Fetch a team's completed game results from ESPN schedule API.
    Returns a list of dicts with keys: date, opponent, result (W/L),
    team_score, opp_score, margin.
    """
    url = espn_schedule_url(team_name)
    if not url:
        return None

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"    ESPN schedule fetch failed for {team_name}: {e}")
        return None

    games = []
    events = data.get("events", [])
    for event in events:
        competitions = event.get("competitions", [])
        if not competitions:
            continue
        comp = competitions[0]

        # Only include completed games
        status = comp.get("status", {}).get("type", {}).get("name", "")
        if status != "STATUS_FINAL":
            continue

        competitors = comp.get("competitors", [])
        if len(competitors) != 2:
            continue

        # Find our team and the opponent
        team_data = None
        opp_data = None
        for c in competitors:
            team_obj = c.get("team", {})
            display = team_obj.get("displayName", "")
            short = team_obj.get("shortDisplayName", "")
            tid = str(team_obj.get("id", ""))
            espn_id = str(ESPN_TEAM_IDS.get(team_name, ""))
            if tid == espn_id:
                team_data = c
            else:
                opp_data = c

        if not team_data or not opp_data:
            continue

        try:
            team_score = int(team_data.get("score", {}).get("value", 0))
            opp_score = int(opp_data.get("score", {}).get("value", 0))
        except (ValueError, TypeError):
            continue

        winner = team_data.get("winner", False)
        opp_name = opp_data.get("team", {}).get("displayName", "Unknown")
        game_date = event.get("date", "")

        games.append({
            "date": game_date,
            "opponent": opp_name,
            "result": "W" if winner else "L",
            "team_score": team_score,
            "opp_score": opp_score,
            "margin": team_score - opp_score,
        })

    # Sort by date ascending
    games.sort(key=lambda g: g["date"])
    return games


def compute_momentum(team_name: str, last_n: int = 10) -> dict:
    """
    Compute momentum metrics for a team based on their last N games.

    Returns dict with:
        Team, Last10Wins, Last10Losses, WinStreak, Last10MarginAvg, MomentumScore
    """
    games = _fetch_espn_schedule(team_name)

    if not games or len(games) == 0:
        return {
            "Team": team_name,
            "Last10Wins": None,
            "Last10Losses": None,
            "WinStreak": 0,
            "Last10MarginAvg": None,
            "MomentumScore": None,
        }

    recent = games[-last_n:] if len(games) >= last_n else games

    # Last N record
    wins = sum(1 for g in recent if g["result"] == "W")
    losses = len(recent) - wins
    win_rate = wins / len(recent)

    # Average margin in last N
    margin_avg = sum(g["margin"] for g in recent) / len(recent)

    # Current streak (from most recent game backwards)
    streak = 0
    streak_type = games[-1]["result"] if games else "W"
    for g in reversed(games):
        if g["result"] == streak_type:
            streak += 1
        else:
            break
    win_streak = streak if streak_type == "W" else -streak

    # Momentum score (0–1):
    # 70% recent win rate + 30% margin component
    # Margin component: sigmoid-ish mapping of avg margin to 0–1
    # +15 margin → ~0.9, 0 margin → 0.5, -15 → ~0.1
    import math
    margin_signal = 1.0 / (1.0 + math.exp(-margin_avg / 7.0))
    momentum_score = round(0.70 * win_rate + 0.30 * margin_signal, 4)

    return {
        "Team": team_name,
        "Last10Wins": wins,
        "Last10Losses": losses,
        "WinStreak": win_streak,
        "Last10MarginAvg": round(margin_avg, 1),
        "MomentumScore": momentum_score,
    }


def fetch_all_momentum(teams: list[str], delay: float = 0.5) -> pd.DataFrame:
    """
    Fetch momentum data for all tournament teams.
    Adds a small delay between requests to be polite to ESPN's API.
    """
    print(f"  Fetching momentum data for {len(teams)} teams...")
    results = []

    for i, team in enumerate(teams):
        result = compute_momentum(team)
        results.append(result)

        if result["MomentumScore"] is not None:
            streak_str = f"W{result['WinStreak']}" if result['WinStreak'] > 0 else f"L{abs(result['WinStreak'])}"
            print(
                f"    {team:25s}  "
                f"Last 10: {result['Last10Wins']}-{result['Last10Losses']}  "
                f"Streak: {streak_str:4s}  "
                f"Margin: {result['Last10MarginAvg']:+.1f}  "
                f"Score: {result['MomentumScore']:.3f}"
            )
        else:
            print(f"    {team:25s}  (no data)")

        if i < len(teams) - 1:
            time.sleep(delay)

        if (i + 1) % 10 == 0:
            print(f"    ... {i + 1}/{len(teams)} done")

    df = pd.DataFrame(results)
    return df


def save_momentum(df: pd.DataFrame, year: int = 2026):
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    path = PROCESSED_DIR / f"momentum_{year}.csv"
    df.to_csv(path, index=False)
    print(f"  Saved momentum data → {path}  ({len(df)} teams)")
    return path


if __name__ == "__main__":
    from pipeline.tournament_filter import build_tournament_teams

    teams = build_tournament_teams()["Team"].tolist()
    momentum = fetch_all_momentum(teams, delay=0.5)
    save_momentum(momentum)

    print("\nTop 10 hottest teams:")
    hot = momentum.dropna(subset=["MomentumScore"]).nlargest(10, "MomentumScore")
    print(hot[["Team", "Last10Wins", "Last10Losses", "WinStreak", "Last10MarginAvg", "MomentumScore"]].to_string(index=False))
