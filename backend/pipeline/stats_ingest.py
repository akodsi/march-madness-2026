"""
Current season team stats ingestion from Sports-Reference CBB.
No auth required.

Fetches two pages and merges them:
  - School stats:  win/loss, SRS, SOS, points scored/allowed
  - Advanced stats: Pace, ORtg (offensive rating), and shooting profile

Sports-Reference URLs:
  https://www.sports-reference.com/cbb/seasons/men/{year}-school-stats.html
  https://www.sports-reference.com/cbb/seasons/men/{year}-advanced-school-stats.html
"""

import requests
import pandas as pd
from io import StringIO
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw" / "sportsref"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"

CURRENT_YEAR = 2026

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

BASE_URL = "https://www.sports-reference.com/cbb/seasons/men/{year}-{page}.html"


def _fetch_table(year: int, page: str) -> pd.DataFrame:
    url = BASE_URL.format(year=year, page=page)
    print(f"  Fetching {url}")
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    tables = pd.read_html(StringIO(resp.text))
    df = tables[0]

    # Flatten multi-level column headers
    df.columns = [
        "_".join(str(part) for part in col).strip("_ ")
        if isinstance(col, tuple) else col
        for col in df.columns
    ]

    # Drop repeated header rows embedded in the table body
    school_col = next(c for c in df.columns if "School" in c)
    df = df[df[school_col].notna()]
    df = df[df[school_col] != "School"]
    df = df.rename(columns={school_col: "Team"})

    return df.reset_index(drop=True)


def fetch_basic_stats(year: int = CURRENT_YEAR) -> pd.DataFrame:
    """
    Win/loss record, SRS (Simple Rating System), SOS (Strength of Schedule),
    points scored and allowed per game.
    """
    df = _fetch_table(year, "school-stats")

    keep = {
        "Team": "Team",
        "Overall_G": "Games",
        "Overall_W": "Wins",
        "Overall_L": "Losses",
        "Overall_W-L%": "WinPct",
        "Overall_SRS": "SRS",
        "Overall_SOS": "SOS",
        "Points_Tm.": "PtsFor",
        "Points_Opp.": "PtsAgainst",
    }
    df = df[[c for c in keep if c in df.columns]].rename(columns=keep)

    numeric_cols = ["Games", "Wins", "Losses", "WinPct", "SRS", "SOS", "PtsFor", "PtsAgainst"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Points per game (total season points / games)
    if "PtsFor" in df.columns and "Games" in df.columns:
        df["PPG"] = (df["PtsFor"] / df["Games"]).round(1)
        df["OppPPG"] = (df["PtsAgainst"] / df["Games"]).round(1)

    return df


def fetch_advanced_stats(year: int = CURRENT_YEAR) -> pd.DataFrame:
    """
    Pace (possessions/40 min), ORtg (offensive rating per 100 poss),
    and key shooting profile metrics.
    """
    df = _fetch_table(year, "advanced-school-stats")

    keep = {
        "Team": "Team",
        "School Advanced_Pace": "Pace",
        "School Advanced_ORtg": "ORtg",
        "School Advanced_FTr": "FTRate",
        "School Advanced_3PAr": "ThreePARate",
        "School Advanced_TS%": "TrueShooting",
        "School Advanced_TRB%": "ReboundPct",
        "School Advanced_AST%": "AssistPct",
        "School Advanced_TOV%": "TurnoverPct",
    }
    df = df[[c for c in keep if c in df.columns]].rename(columns=keep)

    for col in df.columns:
        if col != "Team":
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def build_team_stats(year: int = CURRENT_YEAR) -> pd.DataFrame:
    """
    Merge basic and advanced stats into a single team profile table.
    Also derives a simple efficiency margin estimate: ORtg minus opponent adjusted score.
    """
    print(f"Fetching {year} team stats from Sports-Reference...")
    basic = fetch_basic_stats(year)
    advanced = fetch_advanced_stats(year)

    # Normalize team names for join (strip suffixes like " NCAA")
    for df in [basic, advanced]:
        df["Team"] = df["Team"].str.replace(r"\s+NCAA$", "", regex=True).str.strip()

    merged = basic.merge(advanced, on="Team", how="left")
    merged["Season"] = year

    # Derived: estimated defensive rating (opponent PPG normalized — lower is better)
    # This is a simple proxy until we integrate true adjusted efficiency data
    if "OppPPG" in merged.columns:
        avg_opp = merged["OppPPG"].median()
        merged["DefProxy"] = (avg_opp - merged["OppPPG"]).round(2)  # positive = better defense

    return merged.sort_values("SRS", ascending=False).reset_index(drop=True)


def save_raw(df: pd.DataFrame, filename: str):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / filename
    df.to_csv(path, index=False)
    print(f"  Saved raw  → {path}  ({len(df)} rows)")


def save_processed(df: pd.DataFrame, filename: str):
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    path = PROCESSED_DIR / filename
    df.to_csv(path, index=False)
    print(f"  Saved processed → {path}  ({len(df)} rows)")


if __name__ == "__main__":
    stats = build_team_stats(CURRENT_YEAR)
    save_raw(stats, f"sportsref_stats_{CURRENT_YEAR}.csv")
    save_processed(stats, f"team_stats_{CURRENT_YEAR}.csv")

    print("\nTop 15 teams by SRS:")
    cols = ["Team", "Wins", "Losses", "WinPct", "SRS", "SOS", "PPG", "OppPPG", "ORtg", "Pace"]
    print(stats[cols].head(15).to_string(index=False))
