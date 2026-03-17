"""
Injury / roster availability pipeline.

Fetches injury reports from ESPN's public API for each tournament team
and computes a team health score.

ESPN injuries API (no auth required):
  site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams/{id}/injuries

Health score (0–1):
  1.0 = fully healthy roster
  Deductions based on number of players out and their estimated importance.
  A starter-level player out costs more than a bench player.

Player importance is estimated from roster position and available stats.
ESPN's injury report includes status: "Out", "Day-To-Day", "Questionable".
"""
from __future__ import annotations

import time
import requests
import pandas as pd
from pathlib import Path

from pipeline.espn_ids import ESPN_TEAM_IDS, espn_injuries_url, espn_roster_url

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
RAW_DIR = Path(__file__).parent.parent / "data" / "raw" / "injuries"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

# Impact weights by injury status (how much does this status hurt the team?)
STATUS_IMPACT = {
    "Out":          1.0,    # Definitely missing — full impact
    "Day-To-Day":   0.4,    # Might play but limited
    "Questionable": 0.3,    # Likely to play but uncertain
    "Doubtful":     0.8,    # Probably out
    "Probable":     0.1,    # Almost certainly plays
}

# Per-player deduction from health score, scaled by importance
# A "star" player out costs ~0.15, a rotation player ~0.06, deep bench ~0.02
IMPORTANCE_TIERS = {
    "star":     0.15,   # top 1–2 players (leading scorer, best defender)
    "starter":  0.10,   # starting lineup
    "rotation": 0.06,   # regular rotation (6th–9th man)
    "bench":    0.02,   # deep bench
}


def _fetch_injuries(team_name: str) -> list[dict] | None:
    """
    Fetch injury report for a team from ESPN.
    Returns list of injured player dicts or None if request fails.
    """
    url = espn_injuries_url(team_name)
    if not url:
        return None

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"    ESPN injuries fetch failed for {team_name}: {e}")
        return None

    injuries = []
    # ESPN returns injuries nested under "items" or directly as a list
    items = data.get("items", data.get("injuries", []))

    for item in items:
        athlete = item.get("athlete", {})
        player_name = athlete.get("displayName", "Unknown")
        position = athlete.get("position", {}).get("abbreviation", "")
        status = item.get("status", "Unknown")
        description = item.get("details", {}).get("detail", "")
        if not description:
            description = item.get("longComment", "")

        injuries.append({
            "player": player_name,
            "position": position,
            "status": status,
            "description": description,
        })

    return injuries


def _estimate_importance(player_index: int, total_injured: int) -> str:
    """
    Rough importance tier based on order in injury report.
    ESPN tends to list more important players first.
    Without per-player stats, we use position in the list as a proxy.
    """
    if player_index == 0 and total_injured <= 3:
        return "star"
    elif player_index < 2:
        return "starter"
    elif player_index < 5:
        return "rotation"
    return "bench"


def compute_health_score(team_name: str) -> dict:
    """
    Compute a team's health score based on their injury report.

    Returns dict with:
        Team, HealthScore (0–1), InjuredCount, KeyPlayersOut (count of
        starters/stars out), InjuryDetails (list of player injury dicts)
    """
    injuries = _fetch_injuries(team_name)

    if injuries is None:
        # API failed — assume healthy (no penalty for missing data)
        return {
            "Team": team_name,
            "HealthScore": 1.0,
            "InjuredCount": 0,
            "KeyPlayersOut": 0,
            "InjuryDetails": [],
        }

    if len(injuries) == 0:
        return {
            "Team": team_name,
            "HealthScore": 1.0,
            "InjuredCount": 0,
            "KeyPlayersOut": 0,
            "InjuryDetails": [],
        }

    total_deduction = 0.0
    key_out = 0

    for i, inj in enumerate(injuries):
        status = inj["status"]
        impact = STATUS_IMPACT.get(status, 0.3)
        tier = _estimate_importance(i, len(injuries))
        deduction = IMPORTANCE_TIERS[tier] * impact
        total_deduction += deduction

        if tier in ("star", "starter") and status in ("Out", "Doubtful"):
            key_out += 1

    # Clamp health score to [0.3, 1.0] — even a devastated roster still plays
    health = max(0.3, round(1.0 - total_deduction, 4))

    return {
        "Team": team_name,
        "HealthScore": health,
        "InjuredCount": len(injuries),
        "KeyPlayersOut": key_out,
        "InjuryDetails": injuries,
    }


def fetch_all_injuries(teams: list[str], delay: float = 0.5) -> tuple[pd.DataFrame, dict]:
    """
    Fetch injury data for all tournament teams.

    Returns:
        - DataFrame with Team, HealthScore, InjuredCount, KeyPlayersOut
        - Dict of {team_name: [injury_details]} for commentary/display
    """
    print(f"  Fetching injury reports for {len(teams)} teams...")
    results = []
    details = {}

    for i, team in enumerate(teams):
        result = compute_health_score(team)
        details[team] = result.pop("InjuryDetails")

        results.append(result)

        status_str = "healthy" if result["HealthScore"] == 1.0 else (
            f"score={result['HealthScore']:.2f}  "
            f"injured={result['InjuredCount']}  "
            f"key_out={result['KeyPlayersOut']}"
        )
        print(f"    {team:25s}  {status_str}")

        if i < len(teams) - 1:
            time.sleep(delay)

        if (i + 1) % 10 == 0:
            print(f"    ... {i + 1}/{len(teams)} done")

    df = pd.DataFrame(results)
    return df, details


def save_injuries(df: pd.DataFrame, details: dict, year: int = 2026):
    import json

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # CSV with health scores (for merging into tournament_teams)
    csv_path = PROCESSED_DIR / f"injuries_{year}.csv"
    df.to_csv(csv_path, index=False)
    print(f"  Saved injury scores → {csv_path}  ({len(df)} teams)")

    # JSON with full injury details (for frontend display)
    json_path = PROCESSED_DIR / f"injury_details_{year}.json"
    with open(json_path, "w") as f:
        json.dump(details, f, indent=2)
    print(f"  Saved injury details → {json_path}")

    return csv_path, json_path


if __name__ == "__main__":
    from pipeline.tournament_filter import build_tournament_teams

    teams = build_tournament_teams()["Team"].tolist()
    df, details = fetch_all_injuries(teams, delay=0.5)
    save_injuries(df, details)

    print("\nTeams with health concerns:")
    concerns = df[df["HealthScore"] < 1.0].sort_values("HealthScore")
    if len(concerns) > 0:
        print(concerns.to_string(index=False))
    else:
        print("  All teams reporting healthy rosters.")
