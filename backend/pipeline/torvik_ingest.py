"""
Bart Torvik current season team stats ingestion.
No auth required — pulls directly from barttorvik.com public endpoints.

Key metrics fetched:
- Adjusted offensive efficiency (AdjOE)
- Adjusted defensive efficiency (AdjDE)
- Adjusted tempo (AdjTempo)
- Luck rating
- Strength of schedule (SOS)
- Recent form (last 10 games derived from game log)
"""

import requests
import pandas as pd
from pathlib import Path
from io import StringIO

RAW_DIR = Path(__file__).parent.parent / "data" / "raw" / "torvik"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"

CURRENT_YEAR = 2026

# Bart Torvik CSV export endpoint
TORVIK_STATS_URL = (
    "https://barttorvik.com/getadvstats.php"
    "?year={year}&csv=1"
)

TORVIK_GAME_LOG_URL = (
    "https://barttorvik.com/team-results.php"
    "?team={team}&year={year}&csv=1"
)


def fetch_team_stats(year: int = CURRENT_YEAR) -> pd.DataFrame:
    """
    Fetch season-level advanced stats for all teams from Bart Torvik.
    Returns one row per team with efficiency and tempo metrics.
    """
    url = TORVIK_STATS_URL.format(year=year)
    print(f"Fetching Torvik stats for {year}...")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    df = pd.read_csv(StringIO(resp.text), header=0)

    # Normalize column names (Torvik columns vary slightly by year)
    df.columns = [c.strip() for c in df.columns]

    rename_map = {
        "Team": "Team",
        "AdjOE": "AdjOE",
        "AdjDE": "AdjDE",
        "AdjTempo": "AdjTempo",
        "Luck": "Luck",
        "AdjOE.1": "SOS_AdjOE",   # opponent-adjusted SOS components
        "AdjDE.1": "SOS_AdjDE",
        "Conf": "Conference",
        "Rk": "Rank",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Derived: efficiency margin (higher = better team)
    if "AdjOE" in df.columns and "AdjDE" in df.columns:
        df["AdjEM"] = df["AdjOE"] - df["AdjDE"]

    df["Season"] = year
    return df


def fetch_recent_form(team_name: str, year: int = CURRENT_YEAR, last_n: int = 10) -> dict:
    """
    Fetch a team's last N game results to compute recent win rate.
    Returns dict with team name, recent_wins, recent_losses, recent_win_rate.
    """
    url = TORVIK_GAME_LOG_URL.format(team=team_name.replace(" ", "%20"), year=year)
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text), header=0)
        df.columns = [c.strip() for c in df.columns]

        # Game results typically have a W/L column
        result_col = next((c for c in df.columns if c in ["Result", "W/L", "Outcome"]), None)
        if result_col is None:
            return {"Team": team_name, "RecentWinRate": None}

        recent = df.tail(last_n)
        wins = (recent[result_col].str.upper() == "W").sum()
        return {
            "Team": team_name,
            "RecentWins": int(wins),
            "RecentLosses": int(last_n - wins),
            "RecentWinRate": round(wins / last_n, 3),
        }
    except Exception as e:
        print(f"  Could not fetch form for {team_name}: {e}")
        return {"Team": team_name, "RecentWinRate": None}


def save_raw(df: pd.DataFrame, filename: str):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / filename
    df.to_csv(path, index=False)
    print(f"Saved raw {len(df)} rows → {path}")


def save_processed(df: pd.DataFrame, filename: str):
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    path = PROCESSED_DIR / filename
    df.to_csv(path, index=False)
    print(f"Saved processed {len(df)} rows → {path}")


if __name__ == "__main__":
    stats = fetch_team_stats(CURRENT_YEAR)
    save_raw(stats, f"torvik_stats_{CURRENT_YEAR}.csv")
    save_processed(stats, f"team_stats_{CURRENT_YEAR}.csv")

    print("\nTop 10 teams by Adjusted Efficiency Margin:")
    if "AdjEM" in stats.columns:
        print(stats.nlargest(10, "AdjEM")[["Team", "AdjOE", "AdjDE", "AdjEM", "Conference"]].to_string(index=False))
