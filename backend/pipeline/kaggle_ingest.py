"""
Kaggle NCAA March Mania dataset ingestion.

Downloads and loads historical tournament data from:
https://www.kaggle.com/competitions/march-machine-learning-mania-2025

Setup: place your kaggle.json API key at ~/.kaggle/kaggle.json
Or manually download and place CSVs in data/raw/kaggle/
"""

import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw" / "kaggle"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"

COMPETITION = "march-machine-learning-mania-2025"

# Key files from the Kaggle dataset
SEED_FILE = "MNCAATourneySeeds.csv"
RESULTS_FILE = "MNCAATourneyCompactResults.csv"
TEAM_FILE = "MTeams.csv"
SEASON_STATS_FILE = "MRegularSeasonCompactResults.csv"


def download_kaggle_data():
    """Download dataset via Kaggle API. Requires ~/.kaggle/kaggle.json."""
    try:
        import kaggle
        print(f"Downloading {COMPETITION} dataset...")
        kaggle.api.competition_download_files(
            COMPETITION,
            path=str(RAW_DIR),
            unzip=True,
            quiet=False,
        )
        print("Download complete.")
    except Exception as e:
        print(f"Kaggle download failed: {e}")
        print(f"Manually place CSVs in {RAW_DIR}")


def load_seeds() -> pd.DataFrame:
    """
    Load tournament seeds by team and season.
    Returns columns: Season, Seed (e.g. 'W01'), TeamID, SeedNum (int 1-16), Region
    """
    df = pd.read_csv(RAW_DIR / SEED_FILE)
    df["SeedNum"] = df["Seed"].str[1:3].astype(int)
    df["Region"] = df["Seed"].str[0]
    return df


def load_tourney_results() -> pd.DataFrame:
    """
    Load historical tournament game results.
    Returns columns: Season, DayNum, WTeamID, WScore, LTeamID, LScore, WLoc, NumOT
    """
    return pd.read_csv(RAW_DIR / RESULTS_FILE)


def load_teams() -> pd.DataFrame:
    """Load team ID to name mapping."""
    return pd.read_csv(RAW_DIR / TEAM_FILE)


def build_seed_matchup_history() -> pd.DataFrame:
    """
    Build a historical win rate table for every seed vs seed matchup.
    Returns a DataFrame indexed by (seed_winner, seed_loser) with win counts.
    """
    seeds = load_seeds()
    results = load_tourney_results()
    teams = load_teams()

    # Merge seed info onto results
    seed_map = seeds[["Season", "TeamID", "SeedNum"]].rename(
        columns={"TeamID": "WTeamID", "SeedNum": "WSeed"}
    )
    results = results.merge(seed_map, on=["Season", "WTeamID"], how="left")

    seed_map2 = seed_map.rename(columns={"WTeamID": "LTeamID", "WSeed": "LSeed"})
    results = results.merge(seed_map2, on=["Season", "LTeamID"], how="left")

    results = results.dropna(subset=["WSeed", "LSeed"])
    results["WSeed"] = results["WSeed"].astype(int)
    results["LSeed"] = results["LSeed"].astype(int)

    # Aggregate win counts per seed matchup
    matchups = (
        results.groupby(["WSeed", "LSeed"])
        .size()
        .reset_index(name="Wins")
    )

    # Build symmetric table: for each (s1, s2) pair, total games and wins for lower seed
    records = []
    for _, row in matchups.iterrows():
        w, l, wins = int(row["WSeed"]), int(row["LSeed"]), int(row["Wins"])
        losses = matchups.loc[
            (matchups["WSeed"] == l) & (matchups["LSeed"] == w), "Wins"
        ].sum()
        total = wins + losses
        if total > 0:
            records.append({
                "FavSeed": min(w, l),
                "UndSeed": max(w, l),
                "FavWins": wins if w < l else losses,
                "UndWins": wins if w > l else losses,
                "Total": total,
                "FavWinRate": round((wins if w < l else losses) / total, 3),
            })

    df = pd.DataFrame(records).drop_duplicates(subset=["FavSeed", "UndSeed"])
    df = df.sort_values(["FavSeed", "UndSeed"]).reset_index(drop=True)
    return df


def save_processed(df: pd.DataFrame, filename: str):
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    path = PROCESSED_DIR / filename
    df.to_csv(path, index=False)
    print(f"Saved {len(df)} rows → {path}")


if __name__ == "__main__":
    if not (RAW_DIR / SEED_FILE).exists():
        download_kaggle_data()

    print("Building seed matchup history...")
    matchup_history = build_seed_matchup_history()
    save_processed(matchup_history, "seed_matchup_history.csv")
    print(matchup_history.head(20).to_string())
