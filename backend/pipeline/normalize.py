"""
Normalize and merge Kaggle historical data with Torvik current season stats
into a unified dataset ready for the prediction engine.
"""

import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"

CURRENT_YEAR = 2026


def load_seed_matchup_history() -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / "seed_matchup_history.csv")


def load_team_stats(year: int = CURRENT_YEAR) -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / f"team_stats_{year}.csv")


def build_team_profiles(year: int = CURRENT_YEAR) -> pd.DataFrame:
    """
    Build a per-team profile combining current stats and a normalized score.
    This is the input the prediction engine will use per team.
    """
    stats = load_team_stats(year)

    # Normalize key metrics to 0–1 scale for rule engine weighting
    for col in ["AdjOE", "AdjDE", "AdjEM", "AdjTempo"]:
        if col in stats.columns:
            min_val = stats[col].min()
            max_val = stats[col].max()
            if col == "AdjDE":
                # Lower defensive efficiency = better, so invert
                stats[f"{col}_norm"] = 1 - (stats[col] - min_val) / (max_val - min_val)
            else:
                stats[f"{col}_norm"] = (stats[col] - min_val) / (max_val - min_val)

    return stats


def build_matchup_dataset() -> pd.DataFrame:
    """
    Join seed matchup history with team profile norms.
    Returns one row per (FavSeed, UndSeed) pair enriched with historical win rates.
    Used by the rule engine to look up base win probability.
    """
    history = load_seed_matchup_history()
    return history


def save_processed(df: pd.DataFrame, filename: str):
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    path = PROCESSED_DIR / filename
    df.to_csv(path, index=False)
    print(f"Saved {len(df)} rows → {path}")


if __name__ == "__main__":
    print("Building team profiles...")
    profiles = build_team_profiles()
    save_processed(profiles, f"team_profiles_{CURRENT_YEAR}.csv")
    print(profiles[["Team", "AdjOE", "AdjDE", "AdjEM"]].head(10).to_string(index=False))

    print("\nLoading matchup history...")
    matchups = build_matchup_dataset()
    print(matchups.head(10).to_string(index=False))
